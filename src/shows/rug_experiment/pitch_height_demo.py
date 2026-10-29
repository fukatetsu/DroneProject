from __future__ import annotations

import asyncio
from typing import Optional

from ...controllers.drone import DroneController
from ...analyzers import HoopAnalyzer
from ..base.show import Show

from ..interaction.pitch_height_control import PitchHeightController


class PitchHeightDemo(Show):
    """離陸して1分間ピッチによる高度制御を行い着陸するショー。

    - takeoff
    - 60秒間 `PitchHeightController` による追従
    - land
    """

    use_media_output = False
    requires_analyzer = True

    def __init__(
        self,
        drone: DroneController,
        analyzer: Optional[HoopAnalyzer] = None,
        poll_interval: float = 0.05,
        deadband_deg: float = 5.0,
        map: float = 60,
        max_speed: int = 40,
        enable_output: bool | None = None,
    ) -> None:
        # follow pattern used by other shows: defer to base with resolved enable_output
        resolved_enable_output = True if enable_output is None else enable_output
        super().__init__(drone, enable_output=resolved_enable_output)

        self.poll_interval = poll_interval
        self.deadband_deg = deadband_deg
        self.map = map
        self.max_speed = max_speed

        self._analyzer = analyzer
        self._running = False

    async def start(self) -> None:
        if self._analyzer is None:
            self._analyzer = HoopAnalyzer()
        self._running = True

    async def run(self) -> None:
        if self._analyzer is None:
            raise RuntimeError("PitchHeightDemo not started")

        controller = PitchHeightController(
            drone=self.drone,
            analyzer=self._analyzer,
            poll_interval=self.poll_interval,
        )

        filtered_pitch = 0.0
        filtered_vz = 0.0

        # 離陸
        await self.drone.takeoff()
        await asyncio.sleep(2)

        # 高度を安定させる
        # 120秒間ピッチ追従（ラグなし）
        filtered_pitch, filtered_vz = await controller.follow_pitch_for_height(
            duration_sec=120,
            filtered_pitch=filtered_pitch,
            filtered_vz=filtered_vz,
            pitch_min=-90,
            pitch_max=90,
            height_min=30,
            height_max=200,
            height_gain=1.0,
            x=0,
            y=0,
            yaw=0,
            max_speed=100,
            apply_lag_seconds=0.0,
        )

        self.drone.send_rc_control(0,0,0,0)


        self.drone.send_rc_control(0,0,0,0)

        # 着陸
        await asyncio.sleep(0.5)

    async def stop(self) -> None:
        """Stop the show: signal controller loops to exit and ensure landing."""
        self._running = False
        try:
            await self.drone.land()
        except Exception:
            pass
