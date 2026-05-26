from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class DroneState:
    battery: int = 0
    height: int = 0
    speed_x: int = 0
    speed_y: int = 0
    speed_z: int = 0
    yaw: int = 0
    pitch: int = 0
    roll: int = 0
