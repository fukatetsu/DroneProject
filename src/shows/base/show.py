from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Awaitable, Callable, Dict

from ...controllers.drone import DroneController
from ...output import MediaController


KeyEvent = Callable[[], Awaitable[None]]


class Show(ABC):
    registry = {}
    use_media_output = False
    requires_analyzer = False

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)

        if cls is not Show:
            Show.registry[cls.__name__] = cls
    
    def __init__(self, drone: DroneController, enable_output: bool = False) -> None:
        self.drone = drone
        self._enable_output = enable_output
        self.media = MediaController(drone, enabled=enable_output)
        self.key_events: Dict[str, KeyEvent] = {}

    async def handle_key(self, key: str) -> None:
        event = self.key_events.get(key.upper())
        if event is not None:
            await event()

    @abstractmethod
    async def start(self) -> None:
        pass

    @abstractmethod
    async def run(self) -> None:
        pass

    @abstractmethod
    async def stop(self) -> None:
        pass

    def set_output_enabled(self, enabled: bool) -> None:
        self._enable_output = enabled
        self.media.set_enabled(enabled)

    async def pause(self) -> None:
        self.drone.send_rc_control(
            0,
            0,
            0,
            0,
        )
    
    async def emergency(self) -> None:
        await self.drone.emergency()
    
    async def land(self) -> None:
        self.drone.send_rc_control(
            0,
            0,
            0,
            0,
        )

        await self.drone.land()
