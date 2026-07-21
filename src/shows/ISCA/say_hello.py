from __future__ import annotations

import asyncio

from ...controllers.drone import DroneController
from ..base.show import Show

from ..motions.height_control import adjust_height, calc_height_vz



class SayHello_ISCA(Show):
    media_output = True
    use_media_output = True

    def __init__(
        self,
        drone: DroneController,
        enable_output: bool | None = None
    ) -> None:

        resolved_enable_output = (
            True if enable_output is None else enable_output
        )

        super().__init__(
            drone,
            enable_output=resolved_enable_output,
        )

        self._running = False

    async def start(self) -> None:
        self.media.set_window(monitor = 0)
        self.media.set_fullscreen(True)
        return None

    async def run(self) -> None:
        await self.drone.takeoff()
        print(f"Battery: {self.drone.state.battery}%")
        # await adjust_height(self.drone, target_height=120)
        await asyncio.sleep(0.5)
        await self.drone.go_xyz_speed(0, 120, 0, 100)
        await asyncio.sleep(0.1)
        # await adjust_height(self.drone, target_height=40, max_speed=100)

        await asyncio.sleep(0.5)
        await self.drone.go_xyz_speed(0, -120, 0, 100)
        await asyncio.sleep(0.1)
        # await adjust_height(self.drone, target_height=120, max_speed=100)

        await asyncio.sleep(0.5)


        await self.drone.go_xyz_speed(0, 120, 0, 100)
        self.media.show_image("Hello/スライド1.PNG")
        await asyncio.sleep(0.1)
        # await adjust_height(self.drone, target_height=40, max_speed=100)

        self.media.show_image("Hello/スライド2.PNG")
        await asyncio.sleep(0.5)
        await self.drone.go_xyz_speed(0, -120, 0, 100)
        self.media.show_image("Hello/スライド3.PNG")
        await asyncio.sleep(0.1)
        # await adjust_height(self.drone, target_height=120,max_speed=100)
        self.media.show_image("Hello/スライド4.PNG")
        await asyncio.sleep(0.5)
        await self.drone.go_xyz_speed(0, -120, 0, 100)
        self.media.show_image("Hello/スライド5.PNG")
        await asyncio.sleep(0.1)
        await self.drone.go_xyz_speed(0, 300, 0, 100)
        self.media.show_image("Hello/スライド6.PNG")
        await asyncio.sleep(1)
        await self.drone.go_xyz_speed(0, -300, 0, 100)
        self.media.show_image("Hello/スライド7.PNG")
        await asyncio.sleep(1)
        await self.drone.go_xyz_speed(0, 300, 0, 100)
        self.media.show_image("Hello/スライド8.PNG")
        await asyncio.sleep(5)
        self.media.show_image("Hello/スライド9.PNG")



    async def stop(self) -> None:
        return None
