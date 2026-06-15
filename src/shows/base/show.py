from __future__ import annotations

from abc import ABC, abstractmethod

from ...controllers.drone import DroneController


class Show(ABC):
    def __init__(self, drone: DroneController) -> None:
        self.drone = drone

    @abstractmethod
    async def start(self) -> None:
        pass

    @abstractmethod
    async def run(self) -> None:
        pass

    @abstractmethod
    async def stop(self) -> None:
        pass
    
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
