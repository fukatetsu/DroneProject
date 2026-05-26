from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ImuState:
    roll: float = 0.0
    pitch: float = 0.0
    yaw: float = 0.0
