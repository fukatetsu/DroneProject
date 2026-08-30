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
        self.media.play_se("SayHelloSingle.mp3")
        await adjust_height(self.drone, target_height=120, max_speed=60)
        await asyncio.sleep(1.0)
        self.drone.send_rc_control(-35, 0, 0, 0)
        await asyncio.sleep(1.0)
        self.drone.send_rc_control(0, 0, 0, 0)
        await asyncio.sleep(2)
        await adjust_height(self.drone, target_height=40, max_speed=100)

        await asyncio.sleep(1.0)
        self.drone.send_rc_control(55, 0, 0, 0)
        await asyncio.sleep(1.3)
        self.drone.send_rc_control(0, 0, 0, 0)
        await asyncio.sleep(2)
        await adjust_height(self.drone, target_height=120, max_speed=60)

        await asyncio.sleep(1.0)


        self.media.play_se("SayHelloSingle.mp3")
        self.media.blend_image(
            "Hello/Black.png",
            "Hello/スライド1.PNG",
            effect="wipe_fade_left",
            duration=2,
        )
        self.drone.send_rc_control(-35, 0, 0, 0)
        await asyncio.sleep(1.0)
        self.drone.send_rc_control(0, 0, 0, 0)
        await asyncio.sleep(2)
        self.media.blend_image(
            "Hello/スライド1.PNG",
            "Hello/スライド2.PNG",
            effect="fade",
            duration=2,
        )
        await adjust_height(self.drone, target_height=40, max_speed=100)

        await asyncio.sleep(1.0)
        self.media.blend_image(
            "Hello/スライド2.PNG",
            "Hello/スライド3.PNG",
            effect="fade",
            duration=2,
        )
        self.drone.send_rc_control(55, 0, 0, 0)
        await asyncio.sleep(1.3)
        self.drone.send_rc_control(0, 0, 0, 0)
        await asyncio.sleep(2)

        self.media.blend_image(
            "Hello/スライド3.PNG",
            "Hello/スライド4.PNG",
            effect="fade",
            duration=2,
        )
        await adjust_height(self.drone, target_height=120,max_speed=60)

        await asyncio.sleep(1.0)
        self.media.blend_image(
            "Hello/スライド4.PNG",
            "Hello/スライド5.PNG",
            effect="fade",
            duration=2,
        )
        self.drone.send_rc_control(35, 0, 0, 0)
        await asyncio.sleep(1.0)
        self.drone.send_rc_control(0, 0, 0, 0)
        await asyncio.sleep(2)
        self.media.play_se("SayHelloSingle.mp3")
        self.media.blend_image(
            "Hello/スライド5.PNG",
            "Hello/スライド6.PNG",
            effect="wipe_fade_left",
            duration=2,
        )

        self.drone.send_rc_control(-45, 0, 0, 0)
        await asyncio.sleep(1.8)
        self.drone.send_rc_control(0, 0, 0, 0)
        await asyncio.sleep(2)
        await asyncio.sleep(0.4)

        self.media.blend_image(
            "Hello/スライド6.PNG",
            "Hello/スライド7.PNG",
            effect="wipe_fade_right",
            duration=2,
        )

        self.drone.send_rc_control(45, 0, 0, 0)
        await asyncio.sleep(1.8)
        self.drone.send_rc_control(0, 0, 0, 0)
        await asyncio.sleep(2)
        await asyncio.sleep(0.5)

        self.media.blend_image(
            "Hello/スライド7.PNG",
            "Hello/スライド8.PNG",
            effect="wipe_fade_left",
            duration=2,
        ) 

        self.drone.send_rc_control(-45, 0, 0, 0)
        await asyncio.sleep(1.8)
        self.drone.send_rc_control(0, 0, 0, 0)
        await asyncio.sleep(2)


        self.media.blend_image(
            "Hello/スライド8.PNG",
            "Hello/Black.png",
            effect="fade",
            duration=2,
        )
        self.media.play_se("SayHi.mp3")
        await asyncio.sleep(2)
        await asyncio.sleep(3)

        self.media.blend_image(
            "Hello/Black.png",
            "Hello/yes.png",
            effect="fade",
            duration=2,
        )
        await asyncio.sleep(2)
        self.media.blend_image(
            "Hello/yes.png",
            "Hello/Black.png",
            effect="fade",
            duration=2,
        )
        await asyncio.sleep(3)



    async def stop(self) -> None:
        return None
