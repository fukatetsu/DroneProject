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
        self.drone.send_rc_control(-60, 0, 0, 0)
        await asyncio.sleep(0.8)

        for _ in range(5):
            fb = max(-8, min(8, int(-0.3 * self.drone.state.speed_y)))
            self.drone.send_rc_control(10, fb, 0, 0)
            await asyncio.sleep(0.15)

            fb = max(-8, min(8, int(-0.3 * self.drone.state.speed_y)))
            self.drone.send_rc_control(60, fb, 0, 0)
            await asyncio.sleep(1.4)

            fb = max(-8, min(8, int(-0.3 * self.drone.state.speed_y)))
            self.drone.send_rc_control(-10, fb, 0, 0)
            await asyncio.sleep(0.15)

            fb = max(-8, min(8, int(-0.3 * self.drone.state.speed_y)))
            self.drone.send_rc_control(-60, fb, 0, 0)
            await asyncio.sleep(1.4)
        

        # 右へ大きく移動
        self.drone.send_rc_control(45, 0, 0, 0)
        await asyncio.sleep(2.6)

        # 横方向の慣性を消す
        self.drone.send_rc_control(-25, 0, 0, 0)
        await asyncio.sleep(0.25)

        # 一瞬止める
        self.drone.send_rc_control(0, 0, 0, 0)
        await asyncio.sleep(0.2)

        # 上昇
        self.drone.send_rc_control(0, 0, 40, 0)
        await asyncio.sleep(1.2)

        # 上昇慣性を消す
        self.drone.send_rc_control(0, 0, -20, 0)
        await asyncio.sleep(0.15)

        # ====================
        # 左移動しながら大きく上下
        # ====================

        self.drone.send_rc_control(-35, 0, -45, 0)
        await asyncio.sleep(0.8)

        # 弱めの反転
        self.drone.send_rc_control(8, 0, 25, 0)
        await asyncio.sleep(0.15)

        self.drone.send_rc_control(-35, 0, 45, 0)
        await asyncio.sleep(0.8)

        # 弱めの反転
        self.drone.send_rc_control(8, 0, -25, 0)
        await asyncio.sleep(0.15)

        self.drone.send_rc_control(-35, 0, -45, 0)
        await asyncio.sleep(0.8)

        # 次の動作へ移るため少し整える
        self.drone.send_rc_control(20, 0, 20, 0)
        await asyncio.sleep(0.20)

        self.drone.send_rc_control(0, 0, 0, 0)
        await asyncio.sleep(0.9)

        # ====================
        # ひし形
        # ====================

        self.drone.send_rc_control(-50, 0, -55, 0)
        await asyncio.sleep(0.9)

        self.drone.send_rc_control(20, 0, 30, 0)
        await asyncio.sleep(0.20)

        self.drone.send_rc_control(-50, 0, 55, 0)
        await asyncio.sleep(0.9)

        self.drone.send_rc_control(0, 0, 0, 0)
        await asyncio.sleep(0.20)

        self.drone.send_rc_control(50, 0, 55, 0)
        await asyncio.sleep(0.9)

        self.drone.send_rc_control(-20, 0, -30, 0)
        await asyncio.sleep(0.20)

        self.drone.send_rc_control(50, 0, -55, 0)
        await asyncio.sleep(0.9)

        self.drone.send_rc_control(-20, 0, 30, 0)
        await asyncio.sleep(0.20)

        # 最後に右へ抜ける
        self.drone.send_rc_control(35, 0, 0, 0)
        await asyncio.sleep(1.0)

        # ====================
        # ひし形
        # ====================

        self.drone.send_rc_control(-50, 0, -55, 0)
        await asyncio.sleep(0.9)

        self.drone.send_rc_control(20, 0, 30, 0)
        await asyncio.sleep(0.20)

        self.drone.send_rc_control(-50, 0, 55, 0)
        await asyncio.sleep(0.9)

        self.drone.send_rc_control(0, 0, 0, 0)
        await asyncio.sleep(0.20)

        self.drone.send_rc_control(50, 0, 55, 0)
        await asyncio.sleep(0.9)

        self.drone.send_rc_control(-20, 0, -30, 0)
        await asyncio.sleep(0.20)

        self.drone.send_rc_control(50, 0, -55, 0)
        await asyncio.sleep(0.9)

        self.drone.send_rc_control(-20, 0, 30, 0)
        await asyncio.sleep(0.20)

        # 最後に右へ抜ける
        self.drone.send_rc_control(35, 0, 0, 0)
        await asyncio.sleep(1.0)

        # ====================
        # ひし形
        # ====================

        self.drone.send_rc_control(-50, 0, -55, 0)
        await asyncio.sleep(0.9)

        self.drone.send_rc_control(20, 0, 30, 0)
        await asyncio.sleep(0.20)

        self.drone.send_rc_control(-50, 0, 55, 0)
        await asyncio.sleep(0.9)

        self.drone.send_rc_control(0, 0, 0, 0)
        await asyncio.sleep(0.20)

        self.drone.send_rc_control(50, 0, 55, 0)
        await asyncio.sleep(0.9)

        self.drone.send_rc_control(-20, 0, -30, 0)
        await asyncio.sleep(0.20)

        self.drone.send_rc_control(50, 0, -55, 0)
        await asyncio.sleep(0.9)

        self.drone.send_rc_control(-20, 0, 30, 0)
        await asyncio.sleep(0.20)

        # 最後に右へ抜ける
        self.drone.send_rc_control(35, 0, 0, 0)
        await asyncio.sleep(1.0)

        # 最終停止
        self.drone.send_rc_control(-20, 0, 0, 0)
        await asyncio.sleep(0.15)

        self.drone.send_rc_control(0, 0, 0, 0)


    async def stop(self) -> None:
        return None
