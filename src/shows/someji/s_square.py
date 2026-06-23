from __future__ import annotations

import asyncio

from ...controllers.drone import DroneController
from ..base.show import Show


class SquareShow_s(Show):
    def __init__(self, drone: DroneController) -> None:
        super().__init__(drone)

    async def start(self) -> None:
        return None

    async def run(self) -> None:
        await self.drone.go_xyz_speed(0,80,0,90)
        await asyncio.sleep(0.05)
        await self.drone.go_xyz_speed(0,-80,0,90)
        await asyncio.sleep(0.05)
        await self.drone.go_xyz_speed(0,80,60,90)
        await asyncio.sleep(0.05)
        await self.drone.go_xyz_speed(0,-80,-30,90)
        await asyncio.sleep(0.05)
        await self.drone.go_xyz_speed(0,80,-30,90)
        await asyncio.sleep(0.05)
        await self.drone.go_xyz_speed(0,-80,20,90)
        await asyncio.sleep(0.05)
        await self.drone.go_xyz_speed(0,40,60,90)
        await asyncio.sleep(0.05)
        await self.drone.go_xyz_speed(0,-40,-80,90)
        await asyncio.sleep(0.05)
        await self.drone.go_xyz_speed(0,-80,80,95)
        await asyncio.sleep(0.05)
        await self.drone.go_xyz_speed(0,0,-80,90)
        await asyncio.sleep(0.05)
        await self.drone.go_xyz_speed(0,80,80,75)
        await asyncio.sleep(0.05)
        await self.drone.go_xyz_speed(0,0,-80,90)
        await asyncio.sleep(0.05)


    async def stop(self) -> None:
        return None
