from __future__ import annotations

import asyncio

from ...controllers.drone import DroneController
from ..base.show import Show


class ButterflyEscapeShow(Show):
    async def start(self) -> None:
        return None

    async def run(self) -> None:

        # =====================================
        # 羽ばたき
        # =====================================

        await self.drone.curve_xyz_speed(
            100, 0, 0,
            100, 100, 0,
            30
        )

        await self.drone.curve_xyz_speed(
            0, 100, 0,
            -100, 100, 0,
            30
        )

        # 演者を見つける
        await self.drone.rotate_clockwise(45)

        await asyncio.sleep(1)

        # =====================================
        # 右へ回避
        # =====================================

        await self.drone.curve_xyz_speed(
            80, 80, 0,
            160, 0, 0,
            40
        )

        # 振り返る
        await self.drone.rotate_counter_clockwise(45)

        # 様子を見る
        await asyncio.sleep(1)

        # 少し近寄る
        await self.drone.move_forward(30)

        await asyncio.sleep(0.5)

        # =====================================
        # 左へ回避
        # =====================================

        await self.drone.curve_xyz_speed(
            -80, -80, 0,
            -160, 0, 0,
            40
        )

        # 振り返る
        await self.drone.rotate_clockwise(45)

        await asyncio.sleep(1)

        # 少し近寄る
        await self.drone.move_forward(30)

        await asyncio.sleep(0.5)

        # =====================================
        # 上へ逃げる
        # =====================================

        await self.drone.curve_xyz_speed(
            0, 100, 100,
            0, 0, 200,
            40
        )

        # 下を見る
        await self.drone.rotate_clockwise(30)

        await asyncio.sleep(1)

        await self.drone.move_down(30)

        await asyncio.sleep(0.5)

        # =====================================
        # 足元へ潜る
        # =====================================

        await self.drone.curve_xyz_speed(
            0, -100, -100,
            0, 0, -200,
            40
        )

        await self.drone.rotate_counter_clockwise(30)

        await asyncio.sleep(1)

        await self.drone.move_forward(20)

        await asyncio.sleep(0.5)

        # =====================================
        # 演者の周囲を舞う
        # =====================================

        await self.drone.curve_xyz_speed(
            120, 0, 0,
            120, 120, 0,
            40
        )

        await self.drone.rotate_counter_clockwise(30)

        await asyncio.sleep(0.5)

        await self.drone.curve_xyz_speed(
            0, 120, 0,
            -120, 120, 0,
            40
        )

        await self.drone.rotate_counter_clockwise(30)

        await asyncio.sleep(0.5)

        await self.drone.curve_xyz_speed(
            -120, 0, 0,
            -120, -120, 0,
            40
        )

        await self.drone.rotate_counter_clockwise(30)

        await asyncio.sleep(0.5)

        await self.drone.curve_xyz_speed(
            0, -120, 0,
            120, -120, 0,
            40
        )

        await self.drone.rotate_counter_clockwise(30)

        await asyncio.sleep(0.5)

    async def stop(self) -> None:
        self.drone.send_rc_control(0, 0, 0, 0)