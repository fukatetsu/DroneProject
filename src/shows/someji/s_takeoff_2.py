from __future__ import annotations

import asyncio

from ...controllers.drone import DroneController
from ..base.show import Show


# s2のドローン離陸

class TakeoffShow_s2(Show):
    async def start(self) -> None:
        return None

    async def run(self) -> None:
        await self.drone.takeoff()
        await asyncio.sleep(1)
        print(f"Battery: {self.drone.state.battery}%")

    async def stop(self) -> None:
        return None