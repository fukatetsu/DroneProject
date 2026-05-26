from __future__ import annotations

from abc import ABC, abstractmethod

from ..models.hoop_state import HoopState
from ..models.imu_state import ImuState


class Analyzer(ABC):

    @property
    @abstractmethod
    def state(self) -> HoopState:
        pass

    @abstractmethod
    def update(self, imu_state: ImuState) -> None:
        pass
