from __future__ import annotations

import asyncio
import contextlib
from typing import Optional

try:
    import cv2
except ImportError:
    cv2 = None

from .drone_controller import DroneController
from ...models.drone_state import DroneState


class MockDroneController(DroneController):
    def __init__(self) -> None:
        self._state = DroneState(battery=100, height=0, speed_x=0, speed_y=0, speed_z=0, yaw=0, pitch=0, roll=0)
        self._command_lock = asyncio.Lock()
        self._connected = False
        self._simulation_task: Optional[asyncio.Task[None]] = None
        self._video_capture: Optional[object] = None
        self._video_stream_active = False
        self._latest_frame = None
        self._video_task: Optional[asyncio.Task[None]] = None

    @property
    def state(self) -> DroneState:
        return self._state

    async def connect(self) -> None:
        self._connected = True
        print("[MockDroneController] connect")
        self._simulation_task = asyncio.create_task(self._simulate_state())

    async def disconnect(self) -> None:
        self._connected = False
        if self._simulation_task is not None:
            self._simulation_task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await self._simulation_task
        if self._video_task is not None:
            self._video_task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await self._video_task
        print("[MockDroneController] disconnect")

    async def takeoff(self) -> None:
        print("[MockDroneController] takeoff")
        self._state = self._state.__class__(
            battery=self._state.battery,
            height=100,
            speed_x=0,
            speed_y=0,
            speed_z=0,
            yaw=self._state.yaw,
            pitch=self._state.pitch,
            roll=self._state.roll,
        )

    async def land(self) -> None:
        print("[MockDroneController] land")
        self._state = self._state.__class__(
            battery=self._state.battery,
            height=0,
            speed_x=0,
            speed_y=0,
            speed_z=0,
            yaw=self._state.yaw,
            pitch=self._state.pitch,
            roll=self._state.roll,
        )

    async def emergency(self) -> None:
        print("[MockDroneController] emergency")
        self._state = self._state.__class__(
            battery=self._state.battery,
            height=0,
            speed_x=0,
            speed_y=0,
            speed_z=0,
            yaw=self._state.yaw,
            pitch=self._state.pitch,
            roll=self._state.roll,
        )

    async def flip(self, direction: str) -> None:
        print(f"[MockDroneController] flip({direction})")

    async def move_up(self, distance: int) -> None:
        async with self._command_lock:
            print(f"[MockDroneController] move_up({distance})")

    async def move_down(self, distance: int) -> None:
        async with self._command_lock:
            print(f"[MockDroneController] move_down({distance})")

    async def move_left(self, distance: int) -> None:
        async with self._command_lock:
            print(f"[MockDroneController] move_left({distance})")

    async def move_right(self, distance: int) -> None:
        async with self._command_lock:
            print(f"[MockDroneController] move_right({distance})")

    async def move_forward(self, distance: int) -> None:
        async with self._command_lock:
            print(f"[MockDroneController] move_forward({distance})")

    async def move_back(self, distance: int) -> None:
        async with self._command_lock:
            print(f"[MockDroneController] move_back({distance})")

    async def rotate_clockwise(self, angle: int) -> None:
        async with self._command_lock:
            print(f"[MockDroneController] rotate_clockwise({angle})")

    async def rotate_counter_clockwise(self, angle: int) -> None:
        async with self._command_lock:
            print(f"[MockDroneController] rotate_counter_clockwise({angle})")

    async def go_xyz_speed(self, x: int, y: int, z: int, speed: int) -> None:
        async with self._command_lock:
            print(f"[MockDroneController] go_xyz_speed({x}, {y}, {z}, {speed})")

    async def curve_xyz_speed(
        self,
        x1: int,
        y1: int,
        z1: int,
        x2: int,
        y2: int,
        z2: int,
        speed: int,
    ) -> None:
        async with self._command_lock:
            print(
                f"[MockDroneController] curve_xyz_speed({x1}, {y1}, {z1}, {x2}, {y2}, {z2}, {speed})"
            )

    async def _simulate_state(self) -> None:
        try:
            while self._connected:
                if self._state.speed_z != 0:
                    next_height = self._state.height + int(self._state.speed_z * 0.1)
                    next_height = max(0, next_height)
                    self._state = self._state.__class__(
                        battery=self._state.battery,
                        height=next_height,
                        speed_x=self._state.speed_x,
                        speed_y=self._state.speed_y,
                        speed_z=self._state.speed_z,
                        yaw=self._state.yaw,
                        pitch=self._state.pitch,
                        roll=self._state.roll,
                    )
                await asyncio.sleep(0.1)
        except asyncio.CancelledError:
            pass

    def send_rc_control(self, left_right: int, forward_back: int, up_down: int, yaw: int) -> None:
        if self._command_lock.locked():
            return
        self._state = self._state.__class__(
            battery=self._state.battery,
            height=self._state.height,
            speed_x=left_right,
            speed_y=forward_back,
            speed_z=up_down,
            yaw=self._state.yaw,
            pitch=self._state.pitch,
            roll=self._state.roll,
        )
        print(f"[MockDroneController] send_rc_control({left_right}, {forward_back}, {up_down}, {yaw})")

    def start_video_stream(self) -> None:
        if cv2 is None:
            raise ImportError("opencv-python is required for video stream")
        self._video_capture = cv2.VideoCapture(0)
        self._video_stream_active = True
        # Start background task to continuously capture frames
        if self._video_task is None:
            try:
                loop = asyncio.get_event_loop()
                self._video_task = loop.create_task(self._capture_frames())
            except RuntimeError:
                # No event loop in current thread
                pass
        print("[MockDroneController] start_video_stream")

    def stop_video_stream(self) -> None:
        self._video_stream_active = False
        if self._video_task is not None:
            self._video_task.cancel()
            self._video_task = None
        if self._video_capture is not None:
            self._video_capture.release()
            self._video_capture = None
        self._latest_frame = None
        print("[MockDroneController] stop_video_stream")

    def get_video_frame(self):
        """Get the latest buffered video frame (non-blocking)."""
        return self._latest_frame

    async def _capture_frames(self) -> None:
        """Background task to continuously capture frames."""
        try:
            loop = asyncio.get_event_loop()
            while self._video_stream_active:
                try:
                    if self._video_capture is not None:
                        ret, frame = await loop.run_in_executor(None, self._video_capture.read)
                        if ret:
                            # Convert BGR to RGB
                            if cv2 is not None:
                                frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                            self._latest_frame = frame
                except Exception:
                    pass
                
                # Small sleep to allow other tasks to run
                await asyncio.sleep(0.01)
        except asyncio.CancelledError:
            self._latest_frame = None
