from __future__ import annotations

from abc import ABC, abstractmethod


class InputDevice(ABC):

    @abstractmethod
    async def start(self) -> None:
        pass

    @abstractmethod
    async def stop(self) -> None:
        pass
