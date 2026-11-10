from __future__ import annotations

import asyncio

from ...controllers.drone import DroneController
from ..base.show import Show

from ..motions.arc_move import arc_move
from ..motions.rc_control import rc_control_for, alternate_rc_control_for
from src.shows.motions.height_control import adjust_height



class ParallelSlide(Show):
    use_media_output = True
    def __init__(self, drone: DroneController,enable_output: bool | None = None) -> None:
        resolved_enable_output = (
            True if enable_output is None else enable_output
        )
        super().__init__(drone,enable_output=resolved_enable_output)

    async def start(self) -> None:
        return None

    async def run(self) -> None:
        await asyncio.sleep(1)
        await self.drone.takeoff()
        self.drone.send_rc_control(0,0,0,0)
        await arc_move(self.drone, yaw = 0, duration = 3, ud = -20, target_height = 60)
        await asyncio.sleep(1.0)
        self.media.set_bgm_volume(0)
        self.media.play_bgm("FreeMoveFull.mp3")
        self.media.fade_bgm_volume(100, 1)
        await asyncio.sleep(1.0)

        # 画面左から右にゆっくりとスライドする
        # 演者も左から右へと動いていく
        await alternate_rc_control_for(self.drone, (0, 30, 40, 0), (0, 30, -40, 0), duration=5.0, interval=2.5, does_send_zero=False)
        # await rc_control_for(self.drone, (0, 30, 0, 0), duration=5.0)
        # await rc_control_for(self.drone, (20, 30, 0, -25), duration=2.5)
        # await rc_control_for(self.drone, (-20, 30, 0, 25), duration=2.5)
        # await rc_control_for(self.drone, (0, 100, 0, 0), duration=2.0)


        # 急に上昇しながら半分回転する
        # 演者はいったん下に踏み込んだ後すぐに上に上がっていく

        await arc_move(self.drone, yaw = 73, duration = 3, ud = 90, lr = 40, target_height = 110)

        # 両者が右から左へと動く
        await rc_control_for(self.drone, (0, 30, 0, 0), duration=5.0)
        # await rc_control_for(self.drone, (0, 100, 0, 0), duration=2.0)

        # ドローンは半回転しながらやや下降する
        # 演者はターンしてやや下降する

        await arc_move(self.drone, yaw = -73, duration = 3, ud = -30, lr = -40, target_height = 60)


        # ドローンと目が合う

        self.drone.send_rc_control(0, 0, 0, 0)
        #一瞬アイコンタクト
        await asyncio.sleep(2.0)

        # ドローンが右へと抜けていく

        await rc_control_for(self.drone, (0, 80, 0, 0), duration=2.0)
        self.media.fade_bgm_volume(0, 3.0)
        await asyncio.sleep(3.0)



    async def stop(self) -> None:
        self._running = False
        try:
            await self.drone.land()
        except Exception:
            pass
        return None
