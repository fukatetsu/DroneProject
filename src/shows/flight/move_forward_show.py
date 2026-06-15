from __future__ import annotations

import asyncio

from ...controllers.drone import DroneController
from ..base.show import Show


class MoveForwardShow(Show):
    def __init__(self, drone: DroneController) -> None:
        super().__init__(drone)

    async def start(self) -> None:
        return None

    async def run(self) -> None:
        await self.drone.move_forward(20)
        await asyncio.sleep(0.5)

    async def stop(self) -> None:
        return None
