from __future__ import annotations

import asyncio

from ...controllers.drone import DroneController
from ..base.show import Show


class TakeoffShow(Show):
    async def start(self) -> None:
        print(f"Battery: {self.drone.state.battery}%")
        return None

    async def run(self) -> None:
        await self.drone.takeoff()
        await asyncio.sleep(1)

    async def stop(self) -> None:
        return None
