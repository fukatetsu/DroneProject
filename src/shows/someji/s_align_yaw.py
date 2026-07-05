from __future__ import annotations

import asyncio
import math
import time
from typing import Optional

from ...controllers.drone import DroneController
from ...analyzers import HoopAnalyzer
from ..base.show import Show


def _normalize_angle(angle: float) -> float:
    """Normalize angle to -180..180 degrees."""
    remainder = math.fmod(angle + 180.0, 360.0)
    if remainder < 0:
        remainder += 360.0
    return remainder - 180.0


class AlignYawShow_s(Show):
    """Align drone yaw to hoop yaw using RC yaw commands for a fixed duration.

    - Polls IMU via UDP and runs HoopAnalyzer to get hoop yaw
    - Compares to drone yaw from `drone.state.yaw`
    - Sends `send_rc_control(0,0,0,yaw)` to rotate toward target
    """

    def __init__(
        self,
        drone: DroneController,
        duration_seconds: float = 10.0,
        poll_interval: float = 0.1,
        yaw_tolerance_deg: float = 5.0,
        max_yaw_speed: int = 80,
        gain: float = 10.0,
        analyzer: Optional[HoopAnalyzer] = None,
    ) -> None:
        super().__init__(drone)
        self.duration_seconds = duration_seconds
        # NOTE: shows must not access IMU directly. AlignYawShow reads HoopState
        # from a HoopAnalyzer instance only. The analyzer should be fed by
        # a separate input/producer elsewhere in the application.
        self.poll_interval = poll_interval
        self.yaw_tolerance = yaw_tolerance_deg
        self.max_yaw_speed = int(max(1, min(100, max_yaw_speed)))
        self.gain = gain

        self._analyzer: Optional[HoopAnalyzer] = analyzer
        self._running = False

    async def follow_roll_for(
        self,
        duration_sec: float,
        fb_speed: int = 15,
        gain: float | None = None,
        yaw_tolerance: float | None = None,
        max_yaw_speed: int | None = None,
        poll_interval: float | None = None,
        y_speed: int = 0,
        z_speed: int = 0,
    ) -> None:
        """
        Follow the detected hoop roll for a fixed duration.

        Args:
            duration_sec: Duration to perform control [sec].
            fb_speed: Forward/backward speed (positive = forward).
            gain: Proportional gain for yaw control.
            yaw_tolerance: Deadband for yaw error [deg].
            max_yaw_speed: Maximum yaw speed.
            poll_interval: Control period [sec].
            y_speed: Left/right speed.
            z_speed: Up/down speed.
        """

        gain = self.gain if gain is None else gain
        yaw_tolerance = (
            self.yaw_tolerance if yaw_tolerance is None else yaw_tolerance
        )
        max_yaw_speed = (
            self.max_yaw_speed if max_yaw_speed is None else max_yaw_speed
        )
        poll_interval = (
            self.poll_interval if poll_interval is None else poll_interval
        )

        start_time = time.monotonic()

        while (
            self._running
            and time.monotonic() - start_time < duration_sec
        ):
            # Analyzer output
            hoop_roll = self._analyzer.state.roll
            print(f"Hoop Roll: {hoop_roll}")

            try:
                drone_yaw = self.drone.state.yaw
                print(f"Drone Yaw: {drone_yaw}")
            except Exception:
                drone_yaw = 0.0

            # Shortest angular error
            yaw_error = _normalize_angle(hoop_roll - drone_yaw)

            if abs(yaw_error) <= yaw_tolerance:
                yaw_speed = 0
            else:
                raw = int(gain * yaw_error)

                if raw > 0:
                    yaw_speed = min(max_yaw_speed, raw)
                else:
                    yaw_speed = max(-max_yaw_speed, raw)

            try:
                self.drone.send_rc_control(
                    y_speed,
                    fb_speed,
                    z_speed,
                    yaw_speed,
                )
            except Exception:
                pass

            await asyncio.sleep(poll_interval)

        # Stop after the control period
        try:
            self.drone.send_rc_control(0, 0, 0, 0)
        except Exception:
            pass

    async def start(self) -> None:
        # Do not create or start IMU inputs here. The analyzer should be
        # supplied/updated by external code. If none was provided, create a
        # HoopAnalyzer instance (it will produce default state until updated).
        if self._analyzer is None:
            self._analyzer = HoopAnalyzer()

    async def run(self) -> None:
        if self._analyzer is None:
            raise RuntimeError("AlignYawShow not started")
        await self.follow_roll_for(10.0)
        await self.follow_roll_for(fb_speed=-15, duration_sec=10.0)
        await self.follow_roll_for(fb_speed=15, duration_sec=10.0)
        await self.follow_roll_for(fb_speed=15, duration_sec=5.0, z_speed=10)
        await self.follow_roll_for(fb_speed=15, duration_sec=5.0, z_speed=-10)
        await self.follow_roll_for(fb_speed=15, duration_sec=5.0, z_speed=10)
        await self.follow_roll_for(fb_speed=0, duration_sec=7.0, z_speed=-10)





    async def stop(self) -> None:
        self._running = False
        try:
            self.drone.send_rc_control(0, 0, 0, 0)
        except Exception:
            pass
