from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Sequence


@dataclass(frozen=True)
class ImuState:
    record_id: float = 0.0
    accel_x: float = 0.0
    accel_y: float = 0.0
    accel_z: float = 0.0
    gyro_x: float = 0.0
    gyro_y: float = 0.0
    gyro_z: float = 0.0
    mag_x: float = 0.0
    mag_y: float = 0.0
    mag_z: float = 0.0
    quat_w: float = 1.0
    quat_x: float = 0.0
    quat_y: float = 0.0
    quat_z: float = 0.0
    roll: float = 0.0
    pitch: float = 0.0
    yaw: float = 0.0

    @classmethod
    def from_udp_datapoints(cls, dt: Sequence[float]) -> "ImuState":
        if len(dt) != 14:
            raise ValueError(f"UDP IMU message must contain 14 values, got {len(dt)}")

        record_id = dt[0]
        accel_x = dt[1]
        accel_y = dt[2]
        accel_z = dt[3]
        gyro_x = dt[4]
        gyro_y = dt[5]
        gyro_z = dt[6]
        mag_x = dt[7]
        mag_y = dt[8]
        mag_z = dt[9]
        quat_w = dt[10]
        quat_x = dt[11]
        quat_y = dt[12]
        quat_z = dt[13]

        roll, pitch, yaw = cls.quaternion_to_euler(quat_w, quat_x, quat_y, quat_z)

        return cls(
            record_id=record_id,
            accel_x=accel_x,
            accel_y=accel_y,
            accel_z=accel_z,
            gyro_x=gyro_x,
            gyro_y=gyro_y,
            gyro_z=gyro_z,
            mag_x=mag_x,
            mag_y=mag_y,
            mag_z=mag_z,
            quat_w=quat_w,
            quat_x=quat_x,
            quat_y=quat_y,
            quat_z=quat_z,
            roll=roll,
            pitch=pitch,
            yaw=yaw,
        )

    @classmethod
    def from_udp_message(cls, message: str) -> "ImuState":
        cleaned = message.replace(";\n", "").replace(";", "").strip()
        if not cleaned:
            raise ValueError("UDP IMU message is empty")

        values = [float(x) for x in cleaned.split()]
        return cls.from_udp_datapoints(values)

    @staticmethod
    def quaternion_to_euler(w: float, x: float, y: float, z: float) -> tuple[float, float, float]:
        # Convert quaternion [w, x, y, z] to Euler angles in degrees.
        t0 = 2.0 * (w * x + y * z)
        t1 = 1.0 - 2.0 * (x * x + y * y)
        roll = math.degrees(math.atan2(t0, t1))

        t2 = 2.0 * (w * y - z * x)
        t2 = max(-1.0, min(1.0, t2))
        pitch = math.degrees(math.asin(t2))

        t3 = 2.0 * (w * z + x * y)
        t4 = 1.0 - 2.0 * (y * y + z * z)
        yaw = math.degrees(math.atan2(t3, t4))

        return roll, pitch, yaw
