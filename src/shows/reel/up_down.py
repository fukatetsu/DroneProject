from __future__ import annotations

import asyncio

from ...controllers.drone import DroneController
from ..base.show import Show

from ..motions.arc_move import arc_move
from ..motions.rc_control import rc_control_for, alternate_rc_control_for
from src.shows.motions.height_control import adjust_height



class UpDown(Show):
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




        # 急に上昇しながら半分回転する
        # 演者はいったん下に踏み込んだ後すぐに上に上がっていく

        await arc_move(self.drone, yaw = 73, duration = 6, ud = 0, lr = -40,  target_height = 140, does_send_zero=False)
        await arc_move(self.drone, yaw = 73, duration = 6, ud = 40, lr = -40, fb = -10, target_height = 160)


        await asyncio.sleep(2.0)
        await arc_move(self.drone, yaw = 0, duration = 1, ud = -100, lr = 0, fb = 0, target_height = 100)
        await asyncio.sleep(0.8)
        
        await arc_move(self.drone, yaw = -73, duration = 6, ud = 0, lr = 40, target_height = 60)
        await asyncio.sleep(1.5)
        await arc_move(self.drone, yaw = 0, duration = 1, ud = 100, lr = 0, fb = 0, target_height = 160)
        

        # ドローンは半回転しながらやや下降する
        # 演者はターンしてやや下降する

        await arc_move(self.drone, yaw = 73, duration = 6, ud = -25, lr = -30, target_height = 60)
        await arc_move(self.drone, yaw = -73, duration = 6, ud = -25, lr = -30, target_height = 60)
        await asyncio.sleep(1.5)

        await arc_move(self.drone, yaw = 0, duration = 1, ud = 100, lr = 0, fb = 0, target_height = 120)


        # ドローンと目が合う

        self.drone.send_rc_control(0, 0, 0, 0)
        #一瞬アイコンタクト
        await asyncio.sleep(2.0)

        self.media.fade_bgm_volume(0, 3.0)
        await asyncio.sleep(3.0)



    async def stop(self) -> None:
        self._running = False
        try:
            await self.drone.land()
        except Exception:
            pass
        return None
