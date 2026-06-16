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
        pass

    @abstractmethod
    async def flip(self, direction: str) -> None:
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

    @abstractmethod
    def start_video_stream(self) -> None:
        pass

    @abstractmethod
    def stop_video_stream(self) -> None:
        pass

    @abstractmethod
    def get_video_frame(self):
        pass

    @abstractmethod
    def pause(self) -> None:
        pass

    @property
    @abstractmethod
    def state(self) -> DroneState:
        pass
