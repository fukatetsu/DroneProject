from __future__ import annotations

import asyncio

from ...controllers.drone import DroneController
from ..base.show import Show


class FlipForwardShow(Show):
    def __init__(self, drone: DroneController) -> None:
        super().__init__(drone)

    async def start(self) -> None:
        return None

    async def run(self) -> None:
        await self.drone.flip("f")
        await asyncio.sleep(1.0)

    async def stop(self) -> None:
        return None
