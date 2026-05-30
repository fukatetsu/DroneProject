from __future__ import annotations

import asyncio

from ...controllers.drone import DroneController
from ..base.show import Show


class BounceShow(Show):
    def __init__(self, drone: DroneController) -> None:
        super().__init__(drone)

    async def start(self) -> None:
        return None

    async def run(self) -> None:
        target_height = 100.0
        current_height = float(self.drone.state.height)

        if current_height < target_height:
            await self._reach_height(target_height, speed=20)
        elif current_height > target_height:
            await self._reach_height(target_height, speed=-20)

        amplitude = 10.0
        while True:
            current_height = float(self.drone.state.height)
            up_target = current_height + amplitude
            if up_target >= 130.0:
                await self._reach_height(130.0, speed=20)
                break

            await self._reach_height(up_target, speed=20)

            current_height = float(self.drone.state.height)
            down_target = current_height - amplitude
            if down_target <= 70.0:
                await self._reach_height(70.0, speed=-20)
                break

            await self._reach_height(down_target, speed=-20)
            amplitude += 10.0

    async def stop(self) -> None:
        self.drone.send_rc_control(0, 0, 0, 0)

    async def _reach_height(self, target_height: float, speed: int) -> None:
        current_height = float(self.drone.state.height)
        print(self.drone.state.height)
        if speed > 0:
            if current_height >= target_height:
                return None
        else:
            if current_height <= target_height:
                return None

        self.drone.send_rc_control(0, 0, speed, 0)

        try:
            while True:
                current_height = float(self.drone.state.height)
                if speed > 0 and current_height >= target_height:
                    break
                if speed < 0 and current_height <= target_height:
                    break
                await asyncio.sleep(0.1)
        finally:
            self.drone.send_rc_control(0, 0, 0, 0)
