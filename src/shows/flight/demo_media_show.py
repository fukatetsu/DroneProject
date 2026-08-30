from __future__ import annotations

import asyncio

from ...controllers.drone import DroneController
from ..base.show import Show


class DemoMediaShow(Show):
    """Demo show that exercises the media controller via the show lifecycle."""
    use_media_output = True


    def __init__(self, drone: DroneController, enable_output: bool | None = None) -> None:
        resolved_enable_output = True if enable_output is None else enable_output
        super().__init__(drone, enable_output=resolved_enable_output)
        self._running = False

    async def start(self) -> None:
        self._running = True
        await self.media.enable_camera()
        self.media.set_fullscreen(True)
        self.media.set_window(monitor = 1)

    async def run(self) -> None:
        if not self._running:
            raise RuntimeError("DemoMediaShow not started")

        self.media.show_camera()
        self.media.play_bgm("demo.mp3")
        await asyncio.sleep(5)
        self.media.play_video("demo.MOV")
        await asyncio.sleep(5)
        self.media.show_image("title.png")
        await asyncio.sleep(3)
        self.media.show_black()

    async def stop(self) -> None:
        self._running = False
        self.media.stop_video()
        self.media.stop_bgm()
        await self.media.disable_camera()
