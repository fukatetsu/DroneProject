from __future__ import annotations

import asyncio
import random
import time
from typing import Any, List, Optional, Tuple

try:
    import cv2
except ImportError:  # pragma: no cover - OpenCV is a project dependency
    cv2 = None

from ...analyzers.face_tracking_analyzer import FaceTrackingAnalyzer, VideoFrameUnavailable
from ...controllers.drone import DroneController
from ...models.face_state import FaceDetection, FaceTrackingState
from ..base.show import Show
from ..motions.height_control import adjust_height



class FaceFollowShow(Show):
    requires_face_analyzer = True
    use_media_output = True
    MANUAL_CONTROL_TIMEOUT = 0.35

    def __init__(
        self,
        drone: DroneController,
        analyzer: Optional[FaceTrackingAnalyzer] = None,
        enable_output: bool = True,
        poll_interval: float = 0.1,
        frame_failure_timeout: float = 2.0,
        target_switch_interval: float = 15.0,
        target_lost_grace: float = 1.0,
        deadband: float = 0.08,
        gain: float = 70.0,
        yaw_gain: float = 70.0,
        vertical_target_ratio: float = 0.3,
        max_speed: int = 100,
        rng: Optional[random.Random] = None,
        horizontal_target_ratio: float = 0.5,
    ) -> None:
        super().__init__(drone, enable_output=enable_output)
        if poll_interval <= 0 or frame_failure_timeout <= 0 or target_switch_interval <= 0:
            raise ValueError("Face-follow timing settings must be positive")
        if (
            target_lost_grace < 0
            or deadband < 0
            or gain < 0
            or yaw_gain < 0
            or not 0 < vertical_target_ratio < 1
            or not 0 < horizontal_target_ratio < 1
            or not 1 <= max_speed <= 100
        ):
            raise ValueError("Invalid face-follow control settings")
        self._analyzer = analyzer
        self.poll_interval = poll_interval
        self.frame_failure_timeout = frame_failure_timeout
        self.target_switch_interval = target_switch_interval
        self.target_lost_grace = target_lost_grace
        self.deadband = deadband
        self.gain = gain
        self.yaw_gain = yaw_gain
        self.vertical_target_ratio = vertical_target_ratio
        self.max_speed = max_speed
        self.horizontal_target_ratio = horizontal_target_ratio
        self._rng = rng if rng is not None else random.Random()
        self._running = False
        self._latest_tracking_state: Optional[FaceTrackingState] = None
        self._target_id: Optional[int] = None
        self._target_selected_at = 0.0
        self._target_lost_at: Optional[float] = None
        self._manual_rc: Optional[Tuple[int, int, int, int]] = None
        self._manual_control_until = 0.0
        self.key_events.update(
            {
                "UP": self._move_up,
                "DOWN": self._move_down,
                "LEFT": self._yaw_left,
                "RIGHT": self._yaw_right,
                "1": self._select_target_1,
                "2": self._select_target_2,
                "3": self._select_target_3,
            }
        )

    async def start(self) -> None:
        await adjust_height(self.drone, target_height=120, max_speed=60)
        if self._analyzer is None:
            self._analyzer = FaceTrackingAnalyzer()
        self.media.set_enabled(True)
        self._latest_tracking_state = None
        self._target_id = None
        self._target_lost_at = None
        self._manual_rc = None
        self.media.set_camera_frame_processor(self._annotate_frame)
        try:
            await self.media.enable_camera()
            self.media.show_camera()
        except BaseException:
            self.media.set_camera_frame_processor(None)
            if self.media.is_camera_enabled():
                await self.media.disable_camera()
            self._send_stop()
            raise
        self._running = True

    async def run(self) -> None:
        if self._analyzer is None:
            raise RuntimeError("FaceFollowShow not started")

        frame_failure_since: Optional[float] = None
        try:
            while self._running:
                now = time.monotonic()
                frame = self.drone.get_video_frame()
                try:
                    state = self._analyzer.analyze(
                        frame,
                        captured_at=self.drone.get_video_frame_captured_at(),
                        now=now,
                    )
                except VideoFrameUnavailable as error:
                    self._send_stop()
                    self._latest_tracking_state = None
                    if frame_failure_since is None:
                        frame_failure_since = now
                    elif now - frame_failure_since >= self.frame_failure_timeout:
                        raise RuntimeError(f"Face-follow video input failed: {error}") from error
                    await asyncio.sleep(self.poll_interval)
                    continue

                frame_failure_since = None
                self._latest_tracking_state = state
                detection = self._select_target(state, now)
                self._send_current_command(detection, state, now)
                await asyncio.sleep(self.poll_interval)
        except BaseException:
            self._send_stop()
            raise

    async def stop(self) -> None:
        self._running = False
        try:
            self._send_stop()
        finally:
            self.media.set_camera_frame_processor(None)
            if self.media.is_camera_enabled():
                await self.media.disable_camera()

    def _select_target(self, state: FaceTrackingState, now: float) -> Optional[FaceDetection]:
        candidates = self._numbered_candidates(state)
        by_id = {face.track_id: face for face in candidates}

        if self._target_id in by_id:
            if now - self._target_selected_at >= self.target_switch_interval and len(candidates) > 1:
                alternatives = [face for face in candidates if face.track_id != self._target_id]
                selected = self._rng.choice(alternatives)
                self._target_id = selected.track_id
                self._target_selected_at = now
            self._target_lost_at = None
            return by_id.get(self._target_id)

        if self._target_id is not None:
            if self._target_lost_at is None:
                self._target_lost_at = now
            if now - self._target_lost_at < self.target_lost_grace:
                return None

        if not candidates:
            self._target_id = None
            self._target_lost_at = None
            return None

        selected = self._rng.choice(candidates)
        self._target_id = selected.track_id
        self._target_selected_at = now
        self._target_lost_at = None
        return selected

    @staticmethod
    def _numbered_candidates(state: FaceTrackingState) -> List[FaceDetection]:
        return sorted(state.detections, key=lambda face: face.area, reverse=True)[:3]

    def _select_target_by_number(self, number: int) -> None:
        state = self._latest_tracking_state
        if state is None:
            return
        candidates = self._numbered_candidates(state)
        if number > len(candidates):
            return

        selected = candidates[number - 1]
        self._target_id = selected.track_id
        self._target_selected_at = time.monotonic()
        self._target_lost_at = None

    async def _move_up(self) -> None:
        self._set_manual_control(up_down=self.max_speed)

    async def _move_down(self) -> None:
        self._set_manual_control(up_down=-self.max_speed)

    async def _yaw_left(self) -> None:
        self._set_manual_control(yaw=-self.max_speed)

    async def _yaw_right(self) -> None:
        self._set_manual_control(yaw=self.max_speed)

    async def _select_target_1(self) -> None:
        self._select_target_by_number(1)

    async def _select_target_2(self) -> None:
        self._select_target_by_number(2)

    async def _select_target_3(self) -> None:
        self._select_target_by_number(3)

    def _set_manual_control(self, up_down: int = 0, yaw: int = 0) -> None:
        self._manual_rc = (0, 0, up_down, yaw)
        self._manual_control_until = time.monotonic() + self.MANUAL_CONTROL_TIMEOUT

    def _send_current_command(
        self,
        detection: Optional[FaceDetection],
        state: FaceTrackingState,
        now: float,
    ) -> None:
        if self._manual_rc is not None and now < self._manual_control_until:
            self.drone.send_rc_control(*self._manual_rc)
            return

        self._manual_rc = None
        if detection is None:
            self._send_stop()
        else:
            self._send_tracking_command(detection, state)

    def _send_tracking_command(
        self,
        detection: FaceDetection,
        state: FaceTrackingState,
    ) -> None:
        center_x, center_y = detection.center
        # 目標比率を変えると、カメラ取付や画角のずれを補正できる。
        horizontal_target_x = state.frame_width * self.horizontal_target_ratio
        error_x = (center_x - horizontal_target_x) / (state.frame_width / 2)
        vertical_target_y = state.frame_height * self.vertical_target_ratio
        error_y = (center_y - vertical_target_y) / (state.frame_height / 2)
        yaw = self._control_value(error_x, self.yaw_gain)
        up_down = -self._control_value(error_y, self.gain)
        self.drone.send_rc_control(0, 0, up_down, yaw)

    def _control_value(self, error: float, gain: float) -> int:
        if abs(error) <= self.deadband:
            return 0
        value = int(error * gain)
        return max(-self.max_speed, min(self.max_speed, value))

    def _send_stop(self) -> None:
        self.drone.send_rc_control(0, 0, 0, 0)

    def _annotate_frame(self, frame: Any) -> Any:
        if cv2 is None:
            raise RuntimeError("OpenCV is required to display face tracking annotations")

        annotated = frame.copy()
        state = self._latest_tracking_state
        if state is None:
            cv2.putText(
                annotated,
                "Waiting for camera frame",
                (10, 25),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.6,
                (255, 255, 255),
                2,
            )
            return annotated

        candidates = self._numbered_candidates(state)
        candidate_numbers = {
            detection.track_id: index
            for index, detection in enumerate(candidates, start=1)
        }
        for detection in state.detections:
            selected = detection.track_id == self._target_id
            color = (0, 255, 0) if selected else (255, 200, 0)
            cv2.rectangle(
                annotated,
                (detection.x, detection.y),
                (detection.x + detection.width, detection.y + detection.height),
                color,
                2,
            )
            number = candidate_numbers.get(detection.track_id)
            prefix = f"{number}: " if number is not None else ""
            label = (
                f"{prefix}Target {detection.track_id}"
                if selected
                else f"{prefix}Face {detection.track_id}"
            )
            cv2.putText(
                annotated,
                label,
                (detection.x, max(20, detection.y - 8)),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.6,
                color,
                2,
            )

        cv2.putText(
            annotated,
            "Arrows: up/down altitude, left/right yaw",
            (10, 20),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.5,
            (255, 255, 255),
            1,
        )
        target_keys = "Target keys: " + "  ".join(
            f"{index}={self._target_label(detection)}"
            for index, detection in enumerate(candidates, start=1)
        )
        cv2.putText(
            annotated,
            target_keys if candidates else "Target keys: no faces",
            (10, 40),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.5,
            (255, 255, 255),
            1,
        )

        target_x = int(state.frame_width * self.horizontal_target_ratio)
        target_y = int(state.frame_height * self.vertical_target_ratio)
        cv2.line(
            annotated,
            (target_x, 0),
            (target_x, state.frame_height - 1),
            (255, 255, 0),
            1,
        )
        cv2.line(
            annotated,
            (0, target_y),
            (state.frame_width - 1, target_y),
            (255, 255, 0),
            1,
        )

        if not state.detections:
            cv2.putText(
                annotated,
                "No face detected",
                (10, 25),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.6,
                (255, 255, 255),
                2,
            )
        return annotated

    def _target_label(self, detection: FaceDetection) -> str:
        prefix = "Target" if detection.track_id == self._target_id else "Face"
        return f"{prefix} {detection.track_id}"
