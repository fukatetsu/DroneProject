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


class AlignYawShow(Show):
    """Align drone yaw to hoop yaw using RC yaw commands for a fixed duration.

    - Polls IMU via UDP and runs HoopAnalyzer to get hoop yaw
    - Compares to drone yaw from `drone.state.yaw`
    - Sends `send_rc_control(0,0,0,yaw)` to rotate toward target
    """

    def __init__(
        self,
        drone: DroneController,
        duration_seconds: float = 30.0,
        poll_interval: float = 0.1,
        yaw_tolerance_deg: float = 5.0,
        max_yaw_speed: int = 40,
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

    async def start(self) -> None:
        # Do not create or start IMU inputs here. The analyzer should be
        # supplied/updated by external code. If none was provided, create a
        # HoopAnalyzer instance (it will produce default state until updated).
        if self._analyzer is None:
            self._analyzer = HoopAnalyzer()
        self._running = True

    async def run(self) -> None:
        if self._analyzer is None:
            raise RuntimeError("AlignYawShow not started")

        end_time = time.monotonic() + self.duration_seconds

        try:
            while self._running and time.monotonic() < end_time:
                # The analyzer is expected to be updated externally; the show
                # only reads the `HoopState` produced by the analyzer.
                hoop_yaw = self._analyzer.state.yaw
                print(f"Hoop Yaw: {hoop_yaw}")
                try:
                    drone_yaw = self.drone.state.yaw
                    print(f"Drone Yaw: {drone_yaw}")
                except Exception:
                    drone_yaw = 0.0

                # compute shortest angle from drone to hoop
                yaw_error = _normalize_angle(hoop_yaw - drone_yaw)

                if abs(yaw_error) <= self.yaw_tolerance:
                    yaw_speed = 0
                else:
                    # proportional control; scale error to speed range
                    raw = int(self.gain * yaw_error)
                    # keep within bounds
                    if raw > 0:
                        yaw_speed = min(self.max_yaw_speed, raw)
                    else:
                        yaw_speed = max(-self.max_yaw_speed, raw)

                # Send yaw control; other axes zero
                try:
                    self.drone.send_rc_control(0, 0, 0, int(yaw_speed))
                except Exception:
                    pass

                await asyncio.sleep(self.poll_interval)
        finally:
            # stop motion
            try:
                self.drone.send_rc_control(0, 0, 0, 0)
            except Exception:
                pass

    async def stop(self) -> None:
        self._running = False
        try:
            self.drone.send_rc_control(0, 0, 0, 0)
        except Exception:
            pass
