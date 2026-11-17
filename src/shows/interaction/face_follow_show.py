from __future__ import annotations

import asyncio
import random
import time
from typing import Any, Optional

try:
    import cv2
except ImportError:  # pragma: no cover - OpenCV is a project dependency
    cv2 = None

from ...analyzers.face_tracking_analyzer import FaceTrackingAnalyzer, VideoFrameUnavailable
from ...controllers.drone import DroneController
from ...models.face_state import FaceDetection, FaceTrackingState
from ..base.show import Show


class FaceFollowShow(Show):
    requires_face_analyzer = True
    use_media_output = True

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
        gain: float = 50.0,
        yaw_gain: float = 70.0,
        vertical_target_ratio: float = 0.3,
        max_speed: int = 80,
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

    async def start(self) -> None:
        if self._analyzer is None:
            self._analyzer = FaceTrackingAnalyzer()
        self.media.set_enabled(True)
        self._latest_tracking_state = None
        self._target_id = None
        self._target_lost_at = None
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
                if detection is None:
                    self._send_stop()
                else:
                    self._send_tracking_command(detection, state)
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
        candidates = sorted(state.detections, key=lambda face: face.area, reverse=True)[:3]
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
            label = "Target {}".format(detection.track_id) if selected else "Face {}".format(detection.track_id)
            cv2.putText(
                annotated,
                label,
                (detection.x, max(20, detection.y - 8)),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.6,
                color,
                2,
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
