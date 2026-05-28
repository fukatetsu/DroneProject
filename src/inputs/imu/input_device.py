from __future__ import annotations

from abc import ABC, abstractmethod

from ...models.imu_state import ImuState


class InputDevice(ABC):

    @property
    @abstractmethod
    def state(self) -> ImuState:
        pass

    @abstractmethod
    async def start(self) -> None:
        pass

    @abstractmethod
    async def stop(self) -> None:
        pass
