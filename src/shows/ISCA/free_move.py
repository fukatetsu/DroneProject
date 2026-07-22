from __future__ import annotations

import asyncio

from ...controllers.drone import DroneController
from ..base.show import Show


class FreeMove_ISCA(Show):
    use_media_output = True
    def __init__(self, drone: DroneController,enable_output: bool | None = None) -> None:
        resolved_enable_output = (
            True if enable_output is None else enable_output
        )
        super().__init__(drone,enable_output=resolved_enable_output)

    async def start(self) -> None:
        return None

    async def run(self) -> None:
        self.media.play_se("FreeMove.mp3")
        self.drone.send_rc_control(-90, 0, 0, 0)
        await asyncio.sleep(0.4)
        self.drone.send_rc_control(0, 0, 0, 0)
        await asyncio.sleep(1)
        self.drone.send_rc_control(70, 0, -40, 0)
        await asyncio.sleep(0.8)
        self.drone.send_rc_control(0, 0, 0, 0)
        # 停止させて動きをそろえるパート
        await asyncio.sleep(2.2)
        self.drone.send_rc_control(90, 0, 0, 0)
        await asyncio.sleep(0.8)
        self.drone.send_rc_control(-100, 0, 0, 0)
        await asyncio.sleep(0.15)
        self.drone.send_rc_control(-80, 0, 0, 0)
        await asyncio.sleep(1.1)
        self.drone.send_rc_control(10, 0, 0, 0)
        await asyncio.sleep(0.15)
        self.drone.send_rc_control(80, 0, 0, 0)
        await asyncio.sleep(0.4)
        self.drone.send_rc_control(80, 0, 80, 0)
        await asyncio.sleep(0.6)
        self.drone.send_rc_control(-30, 0, -70, 0)
        await asyncio.sleep(1)
        self.drone.send_rc_control(0, 0, 0, 0)
        await asyncio.sleep(0.7)

        # ゆっくり上に動く
        self.drone.send_rc_control(0, 0, 20, 0)
        await asyncio.sleep(3)


        # ====================
        # ひし形
        # ====================

        self.drone.send_rc_control(50, 0, 55, 0)
        await asyncio.sleep(0.9)

        self.drone.send_rc_control(-20, 0, -30, 0)
        await asyncio.sleep(0.20)

        self.drone.send_rc_control(50, 0, -55, 0)
        await asyncio.sleep(0.9)

        self.drone.send_rc_control(0, 0, 0, 0)
        await asyncio.sleep(0.20)

        self.drone.send_rc_control(-50, 0, -55, 0)
        await asyncio.sleep(0.9)

        self.drone.send_rc_control(20, 0, 30, 0)
        await asyncio.sleep(0.20)

        self.drone.send_rc_control(-50, 0, 55, 0)
        await asyncio.sleep(0.9)

        self.drone.send_rc_control(20, 0, -30, 0)
        await asyncio.sleep(0.20)

        # 最後に左へ抜ける
        self.drone.send_rc_control(-65, 0, 0, 0)
        await asyncio.sleep(2.0)

        
        self.drone.send_rc_control(95, 0, 0, 0)
        await asyncio.sleep(1.2)
        # 右へ大きく移動
        self.drone.send_rc_control(65, 0, 0, 0)
        await asyncio.sleep(2.0)

        # 横方向の慣性を消す
        self.drone.send_rc_control(-25, 0, 0, 0)
        await asyncio.sleep(0.15)

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

        self.drone.send_rc_control(-25, 0, -85, 0)
        await asyncio.sleep(0.8)

        # 弱めの反転
        self.drone.send_rc_control(-25, 0, 45, 0)
        await asyncio.sleep(0.15)

        self.drone.send_rc_control(-25, 0, 85, 0)
        await asyncio.sleep(0.8)

        # 弱めの反転
        self.drone.send_rc_control(-25, 0, -55, 0)
        await asyncio.sleep(0.15)

        self.drone.send_rc_control(-25, 0, -100, 0)
        await asyncio.sleep(0.8)
        # 弱めの反転
        self.drone.send_rc_control(-25, 0, 45, 0)
        await asyncio.sleep(0.15)

        self.drone.send_rc_control(-25, 0, 85, 0)
        await asyncio.sleep(0.8)

        # 弱めの反転
        self.drone.send_rc_control(-35, 0, -55, 0)
        await asyncio.sleep(0.15)

        self.drone.send_rc_control(-35, 0, -100, 0)
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

        self.drone.send_rc_control(50, 0, -55, 0)
        await asyncio.sleep(0.9)

        self.drone.send_rc_control(-20, 0, 30, 0)
        await asyncio.sleep(0.20)

        self.drone.send_rc_control(50, 0, 55, 0)
        await asyncio.sleep(0.9)

        self.drone.send_rc_control(0, 0, 0, 0)
        await asyncio.sleep(0.20)

        self.drone.send_rc_control(-50, 0, 55, 0)
        await asyncio.sleep(0.9)

        self.drone.send_rc_control(20, 0, -30, 0)
        await asyncio.sleep(0.20)

        self.drone.send_rc_control(-50, 0, -55, 0)
        await asyncio.sleep(0.9)

        self.drone.send_rc_control(20, 0, 30, 0)
        await asyncio.sleep(0.20)

        # 最後に右へ抜ける
        self.drone.send_rc_control(35, 0, 0, 0)
        await asyncio.sleep(1.0)

        # 最終停止
        self.drone.send_rc_control(-20, 0, 0, 0)
        await asyncio.sleep(0.15)

        self.drone.send_rc_control(0, 0, 0, 0)

        #45.65s


    async def stop(self) -> None:
        return None
