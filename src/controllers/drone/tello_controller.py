from __future__ import annotations

import asyncio
import contextlib
from typing import Optional

try:
    from djitellopy import Tello
except ImportError:  # pragma: no cover
    Tello = None

try:
    import cv2
except ImportError:
    cv2 = None

from ...models.drone_state import DroneState
from .drone_controller import DroneController


class TelloController(DroneController):
    def __init__(self):
        if Tello is None:
            raise ImportError("djitellopy is required to instantiate TelloController")
        self._tello = Tello()
        self._state = DroneState()
        self._monitor_task: Optional[asyncio.Task[None]] = None
        self._stop_event = asyncio.Event()
        self._command_lock = asyncio.Lock()
        self._latest_frame = None
        self._video_task: Optional[asyncio.Task[None]] = None

    @property
    def state(self) -> DroneState:
        return self._state

    async def connect(self):
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, self._tello.connect)
        self._stop_event.clear()
        self._monitor_task = asyncio.create_task(self._monitor_state_loop())

    async def disconnect(self):
        self._stop_event.set()
        if self._monitor_task is not None:
            self._monitor_task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await self._monitor_task
        if self._video_task is not None:
            self._video_task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await self._video_task
        loop = asyncio.get_event_loop()
        if hasattr(self._tello, "end"):
            await loop.run_in_executor(None, self._tello.end)
        elif hasattr(self._tello, "disconnect"):
            await loop.run_in_executor(None, self._tello.disconnect)

    async def takeoff(self):
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, self._tello.takeoff)

    async def land(self):
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, self._tello.land)

    async def emergency(self):
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, self._tello.emergency)

    async def flip(self, direction: str) -> None:
        async with self._command_lock:
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(None, self._tello.flip, direction)

    async def move_up(
        self,
        distance: int,
    ):
        async with self._command_lock:
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(None, self._tello.move_up, distance)

    async def move_down(
        self,
        distance: int,
    ):
        async with self._command_lock:
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(None, self._tello.move_down, distance)

    async def move_left(
        self,
        distance: int,
    ):
        async with self._command_lock:
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(None, self._tello.move_left, distance)

    async def move_right(
        self,
        distance: int,
    ):
        async with self._command_lock:
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(None, self._tello.move_right, distance)

    async def move_forward(
        self,
        distance: int,
    ):
        async with self._command_lock:
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(None, self._tello.move_forward, distance)

    async def move_back(
        self,
        distance: int,
    ):
        async with self._command_lock:
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(None, self._tello.move_back, distance)

    async def rotate_clockwise(
        self,
        angle: int,
    ):
        async with self._command_lock:
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(None, self._tello.rotate_clockwise, angle)

    async def rotate_counter_clockwise(
        self,
        angle: int,
    ):
        async with self._command_lock:
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(None, self._tello.rotate_counter_clockwise, angle)

    async def go_xyz_speed(
        self,
        x: int,
        y: int,
        z: int,
        speed: int,
    ):
        async with self._command_lock:
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(None, self._tello.go_xyz_speed, x, y, z, speed)

    async def curve_xyz_speed(
        self,
        x1: int,
        y1: int,
        z1: int,
        x2: int,
        y2: int,
        z2: int,
        speed: int,
    ):
        async with self._command_lock:
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(None, self._tello.curve_xyz_speed, x1, y1, z1, x2, y2, z2, speed)

    async def pause(self) -> None:
        async with self._command_lock:
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(None, self._tello.send_rc_control, 0, 0, 0, 0)

    

    def send_rc_control(
        self,
        left_right: int,
        forward_back: int,
        up_down: int,
        yaw: int,
    ):
        if self._command_lock.locked():
            return
        self._tello.send_rc_control(left_right, forward_back, up_down, yaw)

    def start_video_stream(self) -> None:
        """Start video stream with background frame capture task."""
        self._tello.streamon()
        # Start background task to continuously capture frames
        if self._video_task is None:
            try:
                loop = asyncio.get_event_loop()
                self._video_task = loop.create_task(self._capture_frames())
            except RuntimeError:
                # No event loop in current thread, will be created when needed
                pass

    def stop_video_stream(self) -> None:
        """Stop video stream and background frame capture task."""
        self._tello.streamoff()
        if self._video_task is not None:
            self._video_task.cancel()
            self._video_task = None
        self._latest_frame = None

    def get_video_frame(self):
        """
        Get the latest buffered video frame from the drone.
        
        Returns RGB frame (non-blocking).
        Returns None if frame is not available yet.
        """
        return self._latest_frame

    async def _capture_frames(self) -> None:
        """
        Background task to continuously capture frames.
        
        This runs independently from command execution,
        ensuring video updates even during drone operations.
        """
        try:
            loop = asyncio.get_event_loop()
            while True:
                try:
                    frame_read = await loop.run_in_executor(None, self._tello.get_frame_read)
                    if frame_read is not None and frame_read.frame is not None:
                        frame = frame_read.frame
                        
                        # Convert BGR to RGB
                        if cv2 is not None:
                            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                        
                        self._latest_frame = frame
                except Exception:
                    pass
                
                # Small sleep to avoid busy waiting and allow other tasks to run
                await asyncio.sleep(0.01)
        except asyncio.CancelledError:
            self._latest_frame = None

    async def _monitor_state_loop(self):
        loop = asyncio.get_event_loop()
        while not self._stop_event.is_set():
            try:
                battery = await loop.run_in_executor(None, self._tello.get_battery)
                height = await loop.run_in_executor(None, self._tello.get_height)
                speed_x = await loop.run_in_executor(None, self._tello.get_speed_x)
                speed_y = await loop.run_in_executor(None, self._tello.get_speed_y)
                speed_z = await loop.run_in_executor(None, self._tello.get_speed_z)
                yaw = await loop.run_in_executor(None, self._tello.get_yaw)
                pitch = await loop.run_in_executor(None, self._tello.get_pitch)
                roll = await loop.run_in_executor(None, self._tello.get_roll)
                
                self._state = DroneState(
                    battery=battery,
                    height=height,
                    speed_x=speed_x,
                    speed_y=speed_y,
                    speed_z=speed_z,
                    yaw=yaw,
                    pitch=pitch,
                    roll=roll,
                )
            except Exception:
                pass
            await asyncio.sleep(0.2)
