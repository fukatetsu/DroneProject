from __future__ import annotations

import asyncio

from ...controllers.drone import DroneController
from ..base.show import Show


class RotateRightShow(Show):
    def __init__(self, drone: DroneController) -> None:
        super().__init__(drone)

    async def start(self) -> None:
        return None

    async def run(self) -> None:
        await self.drone.rotate_clockwise(90)
        await asyncio.sleep(0.5)

    async def stop(self) -> None:
        self.drone.send_rc_control(0, 0, 0, 0)
