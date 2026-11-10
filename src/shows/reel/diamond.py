from __future__ import annotations

import asyncio

from ...controllers.drone import DroneController
from ..base.show import Show

from ..motions.arc_move import arc_move
from ..motions.rc_control import rc_control_for, alternate_rc_control_for
from src.shows.motions.height_control import adjust_height



class Diamond(Show):
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
        await arc_move(self.drone, yaw = 0, duration = 3, ud = 40, target_height = 160)
        await asyncio.sleep(1.0)
        self.media.set_bgm_volume(0)
        self.media.play_bgm("FreeMoveFull.mp3")
        self.media.fade_bgm_volume(100, 1)
        await asyncio.sleep(1.0)

        # 1回転回る

        await arc_move(self.drone, yaw = 53, fb= -50, duration = 2.5,  lr = 5, ud = -40, target_height = 40, does_send_zero= True)
        await asyncio.sleep(3.0)
        await arc_move(self.drone, yaw = 0, fb= 0, duration = 1,  lr = 0, ud = 70, target_height = 120, does_send_zero= True)
        
        await arc_move(self.drone, yaw = 0, fb= 50, duration = 2,  lr = 0, ud = 0, target_height = 70, does_send_zero= True)
        await asyncio.sleep(2.0)
        await arc_move(self.drone, yaw = -53, fb= -50, duration = 2.5,  lr = -10, ud = -40, target_height = 40, does_send_zero= True)
        await asyncio.sleep(2.0)
        await arc_move(self.drone, yaw = 0, fb= 65, duration = 2.3,  lr = 0, ud = 30, target_height = 120, does_send_zero= True)
        await asyncio.sleep(2.0)
        await arc_move(self.drone, yaw = -53, fb= -50, duration = 2.5,  lr = -10, ud = -30, target_height = 40, does_send_zero= True)
        await asyncio.sleep(2.0)
        await arc_move(self.drone, yaw = 0, fb= 50, duration = 1.5,  lr = 0, ud = 0, target_height = 70, does_send_zero= False)
        await arc_move(self.drone, yaw = 0, fb= 0, duration = 2,  lr = 0, ud = 100, target_height = 150, does_send_zero= False)
        await arc_move(self.drone, yaw = 0, fb= 50, duration = 1,  lr = 0, ud = 0, target_height = 150, does_send_zero= True)

        # # 下方向のタメ
        # await arc_move(self.drone, yaw = 53, duration = 1,  lr = -30, ud = -100, target_height = 40, does_send_zero=False)

        # # 急に上昇する
        # await arc_move(self.drone, yaw = 53, duration = 3, ud = 90, lr = -30, target_height = 100)
        
        # await asyncio.sleep(0.7)
        # await arc_move(self.drone, yaw = -53, duration = 6,  lr = 30, ud = -20, target_height=80, does_send_zero=False)
        # # 下方向のタメ
        # await arc_move(self.drone, yaw = -53, duration = 1.5,  lr = 30, ud = -100, target_height = 40, does_send_zero=False)
        # # 急に上昇する
        # await arc_move(self.drone, yaw = -53, duration = 5, ud = 90, lr = 30, target_height = 140, does_send_zero=False)
        # await arc_move(self.drone, yaw = -58, duration = 5, ud = -20, lr = 25, target_height = 120, does_send_zero=False)
        # await arc_move(self.drone, yaw = -63, duration = 5, ud = -20, lr = 20, target_height = 90, does_send_zero=False)
        # await arc_move(self.drone, yaw = -68, duration = 2, ud = -20, lr = 10, target_height = 60, does_send_zero=False)
        # await arc_move(self.drone, yaw = -48, duration = 2, ud = -20, lr = 10, target_height = 60, does_send_zero=False)
        # await arc_move(self.drone, yaw = -28, duration = 1, ud = -20, lr = 10, target_height = 60, does_send_zero=False)
        # await arc_move(self.drone, yaw = -8, duration = 1, ud = -20, lr = 10, target_height = 60, does_send_zero=False)
        # await arc_move(self.drone, yaw = 93, duration = 1.5, ud = 90, lr = 0, target_height = 140, does_send_zero=False)
        # await arc_move(self.drone, yaw = 0, duration = 2, ud = 0, lr = 0, target_height = 140, does_send_zero=True)
        # await arc_move(self.drone, yaw = -30, duration = 4, ud = -90, lr = 0, target_height = 60, does_send_zero=False)






        self.drone.send_rc_control(0, 0, 0, 0)

        self.media.fade_bgm_volume(0, 3.0)
        await asyncio.sleep(3.0)



    async def stop(self) -> None:
        self._running = False
        try:
            await self.drone.land()
        except Exception:
            pass
        return None
