from __future__ import annotations

import asyncio

from ..base.show import Show
from ..motions.arc_move import arc_move


class ArcMoveTestShow(Show):

    async def start(self) -> None:
        return None

    async def run(self) -> None:




        print("Small right arc")

        await arc_move(
            self.drone,
            lr=20,
            ud = 30,
            yaw=80,
            duration=6.0,
        )

        await asyncio.sleep(0.5)

        # =====================================
        # 小さな左旋回
        # =====================================

        print("Small left arc")

        await arc_move(
            self.drone,
            lr=-20,
            ud=-30,
            yaw=-80,
            duration=6.0,
        )

        await asyncio.sleep(0.5)
        
        await arc_move(
            self.drone,
            lr=20,
            ud = 30,
            yaw=80,
            duration=6.0,
        )

        await asyncio.sleep(0.5)

        # =====================================
        # 小さな左旋回
        # =====================================

        print("Small left arc")

        await arc_move(
            self.drone,
            lr=-20,
            ud=-30,
            yaw=-80,
            duration=6.0,
        )

        await asyncio.sleep(0.5)


    async def stop(self) -> None:
        return None