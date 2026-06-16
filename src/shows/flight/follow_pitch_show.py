from __future__ import annotations

import asyncio
from typing import Optional

from ...controllers.drone import DroneController
from ...analyzers import HoopAnalyzer
from ..base.show import Show


class FollowPitchShow(Show):
    """
    Hoop Pitch -> Drone Forward / Backward

    前傾 -> 前進
    後傾 -> 後退
    """

    def __init__(
        self,
        drone: DroneController,
        analyzer: Optional[HoopAnalyzer] = None,
        poll_interval: float = 0.05,
        deadband_deg: float = 5.0,
        gain: float = 2.0,
        max_speed: int = 50,
    ) -> None:
        super().__init__(drone)

        self.poll_interval = poll_interval
        self.deadband_deg = deadband_deg
        self.gain = gain
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

        while self._running:

            pitch = self._analyzer.state.pitch
            print(f"Hoop Pitch: {pitch}")

            # Pitchローパス
            filtered_pitch = (
                0.95 * filtered_pitch
                + 0.05 * pitch
            )

            # デッドバンド
            if abs(filtered_pitch) < self.deadband_deg:
                target_speed = 0.0
            else:
                target_speed = (
                    filtered_pitch * self.gain
                )

            # 最大速度制限
            target_speed = max(
                -self.max_speed,
                min(self.max_speed, target_speed)
            )

            # 速度ローパス
            filtered_speed = (
                0.8 * filtered_speed
                + 0.2 * target_speed
            )

            fb_speed = int(filtered_speed)

            print(
                f"pitch={pitch:.1f}, "
                f"filtered_pitch={filtered_pitch:.1f}, "
                f"speed={fb_speed}"
            )

            try:
                self.drone.send_rc_control(
                    0,          # lr
                    fb_speed,   # fb
                    0,          # ud
                    0,          # yaw
                )
            except Exception:
                pass

            await asyncio.sleep(self.poll_interval)

    async def stop(self) -> None:
        self._running = False