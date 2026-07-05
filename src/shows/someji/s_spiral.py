from __future__ import annotations

import asyncio

from ..base.show import Show
from ..motions.arc_move import arc_move


class SpiralShow_s(Show):

    async def start(self) -> None:
        return None

    async def run(self) -> None:


        print("turn right")


        # 右旋回
        await arc_move(
            self.drone,
            lr=0,
            ud = 0,
            yaw=60,
            duration=9.0,
        )

        await asyncio.sleep(0.3)

        # 上昇

        print("rise spiral")

        await arc_move(
            self.drone,
            lr=10,
            ud=40,
            yaw=60,
            duration=6.0,
            target_height=160,
        )

        # 下降

        print("down spiral")

        
        await arc_move(
            self.drone,
            lr=10,
            ud = -30,
            yaw=-60,
            duration=12.0,
            target_height=30,
        )
        
                # 上昇

        print("rise spiral")

        await arc_move(
            self.drone,
            lr=-15,
            ud=80,
            yaw=80,
            duration=12.0,
            target_height=180,
        )

        # 下降

        print("down spiral")

        
        await arc_move(
            self.drone,
            lr=-15,
            ud = -30,
            yaw=-80,
            duration=6.0,
            target_height=60,
        )

        # 上昇

        print("rise spiral")

        await arc_move(
            self.drone,
            lr=10,
            ud=30,
            yaw=80,
            duration=6.0,
            target_height=110,
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