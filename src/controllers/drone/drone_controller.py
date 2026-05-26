from __future__ import annotations

from abc import ABC, abstractmethod

from ...models.drone_state import DroneState


class DroneController(ABC):

    @abstractmethod
    async def connect(self):
        pass

    @abstractmethod
    async def disconnect(self):
        pass

    @abstractmethod
    async def takeoff(self):
        pass

    @abstractmethod
    async def land(self):
        pass

    @abstractmethod
    async def emergency(self):
        pass

    @abstractmethod
    async def move_up(
        self,
        distance: int,
    ):
        pass

    @abstractmethod
    async def move_down(
        self,
        distance: int,
    ):
        pass

    @abstractmethod
    async def move_left(
        self,
        distance: int,
    ):
        pass

    @abstractmethod
    async def move_right(
        self,
        distance: int,
    ):
        pass

    @abstractmethod
    async def move_forward(
        self,
        distance: int,
    ):
        pass

    @abstractmethod
    async def move_back(
        self,
        distance: int,
    ):
        pass

    @abstractmethod
    async def rotate_clockwise(
        self,
        angle: int,
    ):
        pass

    @abstractmethod
    async def rotate_counter_clockwise(
        self,
        angle: int,
    ):
        pass

    @abstractmethod
    async def go_xyz_speed(
        self,
        x: int,
        y: int,
        z: int,
        speed: int,
    ):
        pass

    @abstractmethod
    def send_rc_control(
        self,
        left_right: int,
        forward_back: int,
        up_down: int,
        yaw: int,
    ):
        pass

    @property
    @abstractmethod
    def state(self) -> DroneState:
        pass
