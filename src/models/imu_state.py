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
    def _normalize_angle_deg(cls, angle: float) -> float:
        remainder = math.fmod(angle + 180.0, 360.0)
        if remainder < 0:
            remainder += 360.0
        return remainder - 180.0

    @classmethod
    def _accel_to_roll_pitch(cls, accel_x: float, accel_y: float, accel_z: float) -> tuple[float, float]:
        roll = math.degrees(math.atan2(accel_y, accel_z))
        pitch = math.degrees(math.atan2(-accel_x, math.hypot(accel_y, accel_z)))
        return roll, pitch

    @classmethod
    def _mag_to_yaw(cls, mag_x: float, mag_y: float, mag_z: float, roll: float, pitch: float) -> float:
        roll_rad = math.radians(roll)
        pitch_rad = math.radians(pitch)

        mag_x_h = mag_x * math.cos(pitch_rad) + mag_z * math.sin(pitch_rad)
        mag_y_h = (
            mag_x * math.sin(roll_rad) * math.sin(pitch_rad)
            + mag_y * math.cos(roll_rad)
            - mag_z * math.sin(roll_rad) * math.cos(pitch_rad)
        )

        yaw = math.degrees(math.atan2(-mag_y_h, mag_x_h))
        return cls._normalize_angle_deg(yaw)

    @classmethod
    def _fuse_angle(cls, gyro_angle: float, measured_angle: float, alpha: float) -> float:
        angle_error = cls._normalize_angle_deg(measured_angle - gyro_angle)
        fused = gyro_angle + (1.0 - alpha) * angle_error
        return cls._normalize_angle_deg(fused)

    @classmethod
    def from_udp_datapoints(
        cls,
        data: Sequence[float],
        previous_state: "ImuState" | None = None,
        dt: float = 0.0,
        alpha: float = 0.98,
    ) -> "ImuState":
        if len(data) != 14:
            raise ValueError(f"UDP IMU message must contain 14 values, got {len(data)}")

        record_id = data[0]
        accel_x = data[1]
        accel_y = data[2]
        accel_z = data[3]
        gyro_x = data[4]
        gyro_y = data[5]
        gyro_z = data[6]
        mag_x = data[7]
        mag_y = data[8]
        mag_z = data[9]

        roll_acc, pitch_acc = cls._accel_to_roll_pitch(accel_x, accel_y, accel_z)
        yaw_mag = cls._mag_to_yaw(mag_x, mag_y, mag_z, roll_acc, pitch_acc)

        if previous_state is None or dt <= 0.0:
            roll = roll_acc
            pitch = pitch_acc
            yaw = yaw_mag
        else:
            gyro_roll = previous_state.roll + gyro_x * dt
            gyro_pitch = previous_state.pitch + gyro_y * dt
            gyro_yaw = previous_state.yaw + gyro_z * dt

            roll = cls._fuse_angle(gyro_roll, roll_acc, alpha)
            pitch = cls._fuse_angle(gyro_pitch, pitch_acc, alpha)
            yaw = cls._fuse_angle(gyro_yaw, yaw_mag, alpha)

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
            roll=roll,
            pitch=pitch,
            yaw=yaw,
        )

    @classmethod
    def from_udp_message(
        cls,
        message: str,
        previous_state: "ImuState" | None = None,
        dt: float = 0.0,
        alpha: float = 0.98,
    ) -> "ImuState":
        cleaned = message.replace(";\n", "").replace(";", "").strip()
        if not cleaned:
            raise ValueError("UDP IMU message is empty")

        values = [float(x) for x in cleaned.split()]
        return cls.from_udp_datapoints(values, previous_state=previous_state, dt=dt, alpha=alpha)


