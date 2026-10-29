from __future__ import annotations

import asyncio
import time
from typing import Optional

from ...controllers.drone import DroneController
from ...analyzers import HoopAnalyzer
from ..motions.height_control import calc_height_vz, adjust_height


class PitchHeightController:
    """Hoop pitch -> target height controller.

    This class extracts the pitch-to-height mapping and the follow loop
    so existing shows can call into it without modifying their files.

    It also leaves a hook for introducing an intentional lag before
    applying the target height to the drone (see `apply_lag_seconds`).
    """

    def __init__(
        self,
        drone: DroneController,
        analyzer: Optional[HoopAnalyzer] = None,
        poll_interval: float = 0.05,
        deadband_deg: float = 5.0,
        max_speed: int = 40,
    ) -> None:
        self.drone = drone
        self.analyzer = analyzer
        self.poll_interval = poll_interval
        self.deadband_deg = deadband_deg
        self.max_speed = max_speed

        self._running = False

    @staticmethod
    def pitch_to_height(
        pitch: float,
        min_pitch: float = -90.0,
        max_pitch: float = 90.0,
        min_height: float = 30.0,
        max_height: float = 180.0,
    ) -> float:
        pitch = max(min_pitch, min(max_pitch, pitch))
        ratio = (pitch - min_pitch) / (max_pitch - min_pitch)
        return min_height + ratio * (max_height - min_height)

    async def follow_pitch_for_height(
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
        max_speed: Optional[int] = None,
        apply_lag_seconds: float = 0.0,
    ) -> tuple[float, float]:
        """Follow hoop pitch and send RC height commands.

        If `apply_lag_seconds` > 0, the target height will be delayed by that
        amount (implemented as a simple FIFO buffer of timestamps and
        target heights). This makes it possible to simulate or introduce an
        intentional lag between detection and command application.
        """

        if max_speed is None:
            max_speed = self.max_speed

        start_time = time.monotonic()

        # queue of (apply_at_time, target_height)
        lag_queue: list[tuple[float, float]] = []

        self._running = True

        while self._running and time.monotonic() - start_time < duration_sec:
            pitch = self.analyzer.state.pitch if self.analyzer is not None else 0.0

            # low-pass filter
            filtered_pitch = 0.5 * filtered_pitch + 0.5 * pitch

            target_height = self.pitch_to_height(
                pitch=filtered_pitch,
                min_pitch=pitch_min,
                max_pitch=pitch_max,
                min_height=height_min,
                max_height=height_max,
            )

            # enqueue with intended application time
            apply_time = time.monotonic() + max(0.0, apply_lag_seconds)
            lag_queue.append((apply_time, target_height))

            # pop oldest entries whose time has come
            now = time.monotonic()
            while lag_queue and lag_queue[0][0] <= now:
                _, height_to_apply = lag_queue.pop(0)

                target_vz = calc_height_vz(
                    drone=self.drone,
                    target_height=height_to_apply,
                    gain=height_gain,
                    max_speed=max_speed,
                )

                filtered_vz = 0.3 * filtered_vz + 0.7 * target_vz

                current_height = self.drone.state.height_tof

                print(
                    f"Target Height: {height_to_apply:.1f} cm "
                    f"Current Height: {current_height:.1f} cm "
                    f"vz: {filtered_vz:.1f}"
                )

                self.drone.send_rc_control(x, y, int(filtered_vz), yaw)

            await asyncio.sleep(self.poll_interval)

        return filtered_pitch, filtered_vz
