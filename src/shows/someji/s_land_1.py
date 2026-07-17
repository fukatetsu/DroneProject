from __future__ import annotations

import asyncio

from ...controllers.drone import DroneController
from ..base.show import Show


#s1のドローン着陸

class LandingShow_s1(Show):
    async def start(self) -> None:
        return None

    async def run(self) -> None:
        print(f"Battery: {self.drone.state.battery}%")
        await self.drone.land()
        await asyncio.sleep(3.0)

    async def stop(self) -> None:
        self.drone.send_rc_control(0, 0, 0, 0)
