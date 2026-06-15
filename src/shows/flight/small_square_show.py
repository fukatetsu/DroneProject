from __future__ import annotations

import asyncio

from ...controllers.drone import DroneController
from ..base.show import Show


class SmallSquareShow(Show):
    def __init__(self, drone: DroneController) -> None:
        super().__init__(drone)

    async def start(self) -> None:
        return None

    async def run(self) -> None:
        await self.drone.move_forward(20)
        await asyncio.sleep(0.3)
        await self.drone.rotate_clockwise(90)
        await asyncio.sleep(0.3)
        await self.drone.move_right(20)
        await asyncio.sleep(0.3)
        await self.drone.rotate_clockwise(90)
        await asyncio.sleep(0.3)
        await self.drone.move_back(20)
        await asyncio.sleep(0.3)
        await self.drone.rotate_clockwise(90)
        await asyncio.sleep(0.3)
        await self.drone.move_left(20)
        await asyncio.sleep(0.3)
        await self.drone.rotate_clockwise(90)
        await asyncio.sleep(0.3)

    async def stop(self) -> None:
        return None
