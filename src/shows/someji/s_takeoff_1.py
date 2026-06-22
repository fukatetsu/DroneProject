from __future__ import annotations

import asyncio

from ...controllers.drone import DroneController
from ..base.show import Show


# 演技開始時のドローン離陸

class TakeoffShow_s1(Show):
    async def start(self) -> None:
        return None

    async def run(self) -> None:
        await self.drone.takeoff()
        await asyncio.sleep(1)
        print(f"Battery: {self.drone.state.battery}%")
        await self.drone.go_xyz_speed(-40, 0, 30, 20)
        await asyncio.sleep(0.5)

    async def stop(self) -> None:
        return None