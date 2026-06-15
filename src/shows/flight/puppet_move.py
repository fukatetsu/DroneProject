from __future__ import annotations

import asyncio

from ..base.show import Show
from ..motions.easing import swing_move


class PuppetShow(Show):

    async def start(self) -> None:
        return None

    async def run(self) -> None:

        # =====================================
        # 左右
        # =====================================

        for _ in range(10):
            await swing_move(
                self.drone,
                lr=80,
                duration=3.0,
            )

            await asyncio.sleep(0.2)

        # =====================================
        # 上下
        # =====================================

        for _ in range(10):
            await swing_move(
                self.drone,
                ud=80,
                duration=3.0,
            )

            await asyncio.sleep(0.2)

        # # =====================================
        # # 前後
        # # =====================================

        # for _ in range(3):
        #     await swing_move(
        #         self.drone,
        #         fb=80,
        #         duration=2.0,
        #     )

        #     await asyncio.sleep(0.2)

        # # =====================================
        # # 左上 ↔ 右下
        # # =====================================

        # for _ in range(2):
        #     await swing_move(
        #         self.drone,
        #         lr=80,
        #         ud=80,
        #         duration=2.5,
        #     )

        #     await asyncio.sleep(0.2)

        # # =====================================
        # # 左前 ↔ 右後
        # # =====================================

        # for _ in range(2):
        #     await swing_move(
        #         self.drone,
        #         lr=80,
        #         fb=80,
        #         duration=2.5,
        #     )

        #     await asyncio.sleep(0.2)

        # # =====================================
        # # 3軸同時
        # # =====================================

        # for _ in range(3):
        #     await swing_move(
        #         self.drone,
        #         lr=80,
        #         fb=80,
        #         ud=80,
        #         duration=3.0,
        #     )

        #     await asyncio.sleep(0.2)

    async def stop(self) -> None:
        self.drone.send_rc_control(0, 0, 0, 0)