from __future__ import annotations

import math
import time
from typing import Optional

from .analyzer import Analyzer
from ..models.hoop_state import HoopState
from ..models.imu_state import ImuState
from ..models.rotation_direction import RotationDirection


def _normalize_angle(angle: float) -> float:
    """角度差を -180..180 に正規化する。"""
    remainder = math.fmod(angle + 180.0, 360.0)
    if remainder < 0:
        remainder += 360.0
    return remainder - 180.0


class HoopAnalyzer(Analyzer):
    def __init__(self) -> None:
        self._state = HoopState()
        self._previous_yaw: Optional[float] = None
        self._previous_time: Optional[float] = None

    @property
    def state(self) -> HoopState:
        return self._state

    def update(self, imu_state: ImuState) -> None:
        current_time = time.monotonic()
        rotation_speed = 0.0
        rotation_direction = RotationDirection.NONE

        if self._previous_yaw is not None and self._previous_time is not None:
            elapsed = current_time - self._previous_time
            if elapsed > 0:
                yaw_diff = _normalize_angle(imu_state.yaw - self._previous_yaw)
                rotation_speed = abs(yaw_diff) / elapsed
                if yaw_diff > 0:
                    rotation_direction = RotationDirection.COUNTER_CLOCKWISE
                elif yaw_diff < 0:
                    rotation_direction = RotationDirection.CLOCKWISE

        self._state = HoopState(
            roll=imu_state.roll,
            pitch=imu_state.pitch,
            yaw=imu_state.yaw,
            rotation_speed=rotation_speed,
            rotation_direction=rotation_direction,
        )
        self._previous_yaw = imu_state.yaw
        self._previous_time = current_time
