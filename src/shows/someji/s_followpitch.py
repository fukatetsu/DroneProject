from __future__ import annotations

import asyncio
from typing import Optional
import time

from ...controllers.drone import DroneController
from ...analyzers import HoopAnalyzer
from ..base.show import Show

from ..motions.height_control import adjust_height, calc_height_vz


class FollowPitchShow_s(Show):
    """
    Hoop Pitch -> Drone Forward / Backward

    前傾 -> 前進
    後傾 -> 後退
    """

    async def _follow_pitch_for_y_speed(
        self,
        duration_sec: float,
        filtered_pitch: float,
        filtered_speed: float,
        x:int = 0,
        yaw:int = 0,
        z:int = 0
    ) -> tuple[float, float]:

        start_time = time.monotonic()

        while (
            self._running
            and time.monotonic() - start_time < duration_sec
        ):
            pitch = self._analyzer.state.pitch
            print(f"Hoop Pitch: {pitch}")


            filtered_pitch = (
                0.5 * filtered_pitch
                + 0.5 * pitch
            )

            if abs(filtered_pitch) < self.deadband_deg:
                target_speed = 0.0
            else:
                target_speed = (
                    filtered_pitch / 60.0
                ) * self.max_speed

            target_speed = max(
                -self.max_speed,
                min(self.max_speed, target_speed),
            )

            filtered_speed = (
                0.3 * filtered_speed
                + 0.7 * target_speed
            )

            self.drone.send_rc_control(
                x,
                int(filtered_speed),
                z,
                yaw,
            )

            await asyncio.sleep(self.poll_interval)

        return filtered_pitch, filtered_speed
    
    @staticmethod
    def pitch_to_height(
        pitch: float,
        min_pitch: float = -90.0,
        max_pitch: float = 90.0,
        min_height: float = 30.0,
        max_height: float = 180.0,
    ) -> float:
        """
        Hoop Pitch を目標高度へ変換する。

        デフォルトでは以下の対応となる。

            -90 deg ->  30 cm
            0 deg -> 105 cm
            +90 deg -> 180 cm

        Args:
            pitch:
                Hoop Pitch [deg]

            min_pitch:
                最小Pitch [deg]

            max_pitch:
                最大Pitch [deg]

            min_height:
                最小高度 [cm]

            max_height:
                最大高度 [cm]

        Returns:
            目標高度 [cm]
        """

        pitch = max(
            min_pitch,
            min(max_pitch, pitch),
        )

        ratio = (
            (pitch - min_pitch)
            / (max_pitch - min_pitch)
        )

        return (
            min_height
            + ratio * (max_height - min_height)
        )
    
    async def _follow_pitch_for_height(
        self,
        duration_sec: float,
        filtered_pitch: float,
        filtered_vz: float,
        pitch_min: float = -90.0,
        pitch_max: float = 90.0,
        height_min: float = 30.0,
        height_max: float = 180.0,
        height_gain: float = 1.0,
        x: int = 0,
        y: int = 0,
        yaw: int = 0,
        max_speed: int = 0
    ) -> tuple[float, float]:
        """
        Hoop Pitchを目標高度へ変換し、
        ドローンの高度を追従させる。

        Pitchは指定された範囲から高度範囲へ線形変換される。

        処理の流れ:

            Hoop Pitch
                ↓
            Low-pass Filter
                ↓
            Target Height
                ↓
            calc_height_vz()
                ↓
            Low-pass Filter
                ↓
            RC Command

        Args:
            duration_sec:
                制御継続時間 [sec]

            filtered_pitch:
                前回までのフィルタ済みPitch

            filtered_vz:
                前回までのフィルタ済み上下速度

            pitch_min:
                Pitch下限 [deg]

            pitch_max:
                Pitch上限 [deg]

            height_min:
                高度下限 [cm]

            height_max:
                高度上限 [cm]

            height_gain:
                高度制御ゲイン

            x:
                左右移動速度 (RC lr)

            y:
                前後移動速度 (RC fb)

            yaw:
                ヨー速度 (RC yaw)

        Returns:
            (
                filtered_pitch,
                filtered_vz,
            )
        """

        max_speed = (self.max_speed if max_speed == None else max_speed)

        start_time = time.monotonic()

        while (
            self._running
            and time.monotonic() - start_time < duration_sec
        ):
            pitch = self._analyzer.state.pitch

            print(
                f"Hoop Pitch: {pitch:.1f}"
            )

            filtered_pitch = (
                0.5 * filtered_pitch
                + 0.5 * pitch
            )

            target_height = self.pitch_to_height(
                pitch=filtered_pitch,
                min_pitch=pitch_min,
                max_pitch=pitch_max,
                min_height=height_min,
                max_height=height_max,
            )

            target_vz = calc_height_vz(
                drone=self.drone,
                target_height=target_height,
                gain=height_gain,
                max_speed=max_speed,
            )

            filtered_vz = (
                0.3 * filtered_vz
                + 0.7 * target_vz
            )

            current_height = (
                self.drone.state.height_tof
            )

            print(
                f"Target Height: {target_height:.1f} cm "
                f"Current Height: {current_height:.1f} cm "
                f"vz: {filtered_vz:.1f}"
            )

            self.drone.send_rc_control(
                x,
                y,
                int(filtered_vz),
                yaw,
            )

            await asyncio.sleep(
                self.poll_interval
            )

        return (
            filtered_pitch,
            filtered_vz,
        )

    def __init__(
        self,
        drone: DroneController,
        analyzer: Optional[HoopAnalyzer] = None,
        poll_interval: float = 0.05,
        deadband_deg: float = 5.0,
        map: float = 60,
        max_speed: int = 40,
    ) -> None:
        super().__init__(drone)

        self.poll_interval = poll_interval
        self.deadband_deg = deadband_deg
        self.map = map
        self.max_speed = max_speed

        self._analyzer: Optional[HoopAnalyzer] = analyzer
        self._running = False

    async def start(self) -> None:
        if self._analyzer is None:
            self._analyzer = HoopAnalyzer()

        self._running = True

    async def run(self) -> None:
        if self._analyzer is None:
            raise RuntimeError("FollowPitchShow not started")

        filtered_pitch = 0.0
        filtered_speed = 0.0
        filtered_vz = 0.0

        filtered_pitch, filtered_vz = (
            await self._follow_pitch_for_height(
                duration_sec=15,
                filtered_pitch=filtered_pitch,
                filtered_vz=filtered_vz,
                pitch_min=-90,
                pitch_max=90,
                height_min=30,
                height_max=200,
                yaw = 20,
                y = 5,
                max_speed=100
            )
        )

        filtered_pitch, filtered_vz = (
            await self._follow_pitch_for_height(
                duration_sec=20,
                filtered_pitch=filtered_pitch,
                filtered_vz=filtered_vz,
                pitch_min=-90,
                pitch_max=90,
                height_min=30,
                height_max=200,
                yaw = -20,
                y = -5,
                max_speed=100
            )
        )

        self.drone.send_rc_control(
                0,          # lr
                0,   # fb
                0,          # ud
                0         # yaw
        )

        await adjust_height(self.drone, target_height=90)
        # asyncio.sleep(4)

        # # 1回目
        # filtered_pitch, filtered_speed = (
        #     await self._follow_pitch_for_y_speed(
        #         20,
        #         filtered_pitch,
        #         filtered_speed,
        #         yaw = 20,

        #     )
        # )
        # self.drone.send_rc_control(
        #         0,          # lr
        #         0,   # fb
        #         0,          # ud
        #         0         # yaw
        # )



        # # 2回目
        # filtered_pitch, filtered_speed = (
        #     await self._follow_pitch_for_y_speed(
        #         20,
        #         filtered_pitch,
        #         filtered_speed,
        #         yaw = -20,
        #     )
        # )
        # filtered_pitch, filtered_speed = (
        #     await self._follow_pitch_for_y_speed(
        #         5,
        #         filtered_pitch,
        #         filtered_speed,
        #         yaw = 0,
        #     )
        # )

        self.drone.send_rc_control(
                0,          # lr
                0,   # fb
                0,          # ud
                0         # yaw
        )

        await asyncio.sleep(2)

        # self.drone.send_rc_control(
        #         0,          # lr
        #         0,   # fb
        #         0,          # ud
        #         0         # yaw
        # )

        # # 3回目
        # filtered_pitch, filtered_speed = (
        #     await self._follow_pitch_for_y_speed(
        #         15,
        #         filtered_pitch,
        #         filtered_speed,
        #     )
        # )



    async def stop(self) -> None:
        self.drone.send_rc_control(
                0,          # lr
                0,   # fb
                0,          # ud
                0          # yaw
            )
        self._running = False