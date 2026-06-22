from __future__ import annotations

import asyncio

from ..base.show import Show
from ..motions.arc_move import arc_move


class CircleShow_s(Show):

    async def start(self) -> None:
        return None

    async def run(self) -> None:


        print("circle")


        # 右旋回
        await arc_move(
            self.drone,
            lr=20,
            ud = 0,
            yaw=30,
            duration=15.0,
        )

        
        
        self.drone.send_rc_control(
            0,
            0,
            0,
            0,
        )
        
        await asyncio.sleep(3.0)
        





    async def stop(self) -> None:
        return None