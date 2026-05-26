from __future__ import annotations

import asyncio
from typing import Optional

from .drone_controller import DroneController
from ...models.drone_state import DroneState


class MockDroneController(DroneController):
    def __init__(self) -> None:
        self._state = DroneState(battery=100, height=0, speed_x=0, speed_y=0, speed_z=0, yaw=0, pitch=0, roll=0)
        self._command_lock = asyncio.Lock()
        self._connected = False

    @property
    def state(self) -> DroneState:
        return self._state

    async def connect(self) -> None:
        self._connected = True
        print("[MockDroneController] connect")

    async def disconnect(self) -> None:
        self._connected = False
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

    def send_rc_control(self, left_right: int, forward_back: int, up_down: int, yaw: int) -> None:
        if self._command_lock.locked():
            return
        print(f"[MockDroneController] send_rc_control({left_right}, {forward_back}, {up_down}, {yaw})")
