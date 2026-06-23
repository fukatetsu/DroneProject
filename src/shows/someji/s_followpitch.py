from __future__ import annotations

import asyncio
from typing import Optional
import time

from ...controllers.drone import DroneController
from ...analyzers import HoopAnalyzer
from ..base.show import Show


class FollowPitchShow_s(Show):
    """
    Hoop Pitch -> Drone Forward / Backward

    前傾 -> 前進
    後傾 -> 後退
    """

    async def _follow_pitch_for(
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

        # 1回目
        filtered_pitch, filtered_speed = (
            await self._follow_pitch_for(
                15,
                filtered_pitch,
                filtered_speed,
            )
        )
        self.drone.send_rc_control(
                0,          # lr
                0,   # fb
                0,          # ud
                0         # yaw
        )



        # 2回目
        filtered_pitch, filtered_speed = (
            await self._follow_pitch_for(
                15,
                filtered_pitch,
                filtered_speed,
            )
        )

        self.drone.send_rc_control(
                0,          # lr
                0,   # fb
                0,          # ud
                0         # yaw
        )

        # 3回目
        filtered_pitch, filtered_speed = (
            await self._follow_pitch_for(
                15,
                filtered_pitch,
                filtered_speed,
            )
        )



    async def stop(self) -> None:
        self.drone.send_rc_control(
                0,          # lr
                0,   # fb
                0,          # ud
                0          # yaw
            )
        self._running = False