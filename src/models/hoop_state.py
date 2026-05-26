from __future__ import annotations

from dataclasses import dataclass

from .rotation_direction import RotationDirection


@dataclass(frozen=True)
class HoopState:
    roll: float = 0.0
    pitch: float = 0.0
    yaw: float = 0.0
    rotation_speed: float = 0.0
    rotation_direction: RotationDirection = RotationDirection.NONE
