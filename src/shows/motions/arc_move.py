from __future__ import annotations

import asyncio
import time

from ...controllers.drone import DroneController


async def arc_move(
    drone: DroneController,
    lr: int = 0,
    yaw: int = 0,
    duration: float = 1.0,
    fb: int = 0,
    ud: int = 0,
    interval: float = 0.05,
) -> None:
    """
    円弧移動

    Parameters
    ----------
    drone : DroneController
        ドローン

    lr : int
        左右速度 (-100 ~ 100)

    yaw : int
        ヨー速度 (-100 ~ 100)

    duration : float
        継続時間 [s]

    fb : int
        前後速度 (-100 ~ 100)

    ud : int
        上下速度 (-100 ~ 100)
    """

    end_time = time.monotonic() + duration

    while time.monotonic() < end_time:
        drone.send_rc_control(
            lr,
            fb,
            ud,
            yaw,
        )

        await asyncio.sleep(interval)

    drone.send_rc_control(
        0,
        0,
        0,
        0,
    )