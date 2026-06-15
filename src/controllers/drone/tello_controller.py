from __future__ import annotations

import asyncio
import contextlib
from typing import Optional

try:
    from djitellopy import Tello
except ImportError:  # pragma: no cover
    Tello = None

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

    @property
    def state(self) -> DroneState:
        return self._state

    async def connect(self):
        self._tello.connect()
        self._stop_event.clear()
        self._monitor_task = asyncio.create_task(self._monitor_state_loop())

    async def disconnect(self):
        self._stop_event.set()
        if self._monitor_task is not None:
            self._monitor_task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await self._monitor_task
        if hasattr(self._tello, "end"):
            self._tello.end()
        elif hasattr(self._tello, "disconnect"):
            self._tello.disconnect()

    async def takeoff(self):
        self._tello.takeoff()

    async def land(self):
        self._tello.land()

    async def emergency(self):
        self._tello.emergency()

    async def flip(self, direction: str) -> None:
        async with self._command_lock:
            self._tello.flip(direction)

    async def move_up(
        self,
        distance: int,
    ):
        async with self._command_lock:
            self._tello.move_up(distance)

    async def move_down(
        self,
        distance: int,
    ):
        async with self._command_lock:
            self._tello.move_down(distance)

    async def move_left(
        self,
        distance: int,
    ):
        async with self._command_lock:
            self._tello.move_left(distance)

    async def move_right(
        self,
        distance: int,
    ):
        async with self._command_lock:
            self._tello.move_right(distance)

    async def move_forward(
        self,
        distance: int,
    ):
        async with self._command_lock:
            self._tello.move_forward(distance)

    async def move_back(
        self,
        distance: int,
    ):
        async with self._command_lock:
            self._tello.move_back(distance)

    async def rotate_clockwise(
        self,
        angle: int,
    ):
        async with self._command_lock:
            self._tello.rotate_clockwise(angle)

    async def rotate_counter_clockwise(
        self,
        angle: int,
    ):
        async with self._command_lock:
            self._tello.rotate_counter_clockwise(angle)

    async def go_xyz_speed(
        self,
        x: int,
        y: int,
        z: int,
        speed: int,
    ):
        async with self._command_lock:
            self._tello.go_xyz_speed(x, y, z, speed)

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
            self._tello.curve_xyz_speed(x1, y1, z1, x2, y2, z2, speed)

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

    async def _monitor_state_loop(self):
        while not self._stop_event.is_set():
            try:
                self._state = DroneState(
                    battery=self._tello.get_battery(),
                    height=self._tello.get_height(),
                    speed_x=self._tello.get_speed_x(),
                    speed_y=self._tello.get_speed_y(),
                    speed_z=self._tello.get_speed_z(),
                    yaw=self._tello.get_yaw(),
                    pitch=self._tello.get_pitch(),
                    roll=self._tello.get_roll(),
                )
            except Exception:
                pass
            await asyncio.sleep(0.2)
