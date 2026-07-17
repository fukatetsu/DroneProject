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
    interval: float = 0.1,
    target_height: int = None,
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
    isHeightReached = False

    end_time = time.monotonic() + duration

    while time.monotonic() < end_time:

        # 高度の確認
        if target_height is not None and not isHeightReached:
            current_height = drone.state.height_tof
            error = target_height - current_height

            reached = (
                (ud > 0 and current_height >= target_height)
                or
                (ud < 0 and current_height <= target_height)
            )

            if reached:
                isHeightReached = True
                print(f"Target height reached: {current_height} cm")

        #  コマンドの送信
        if target_height is None or (target_height is not None and  not isHeightReached):
            drone.send_rc_control(
                lr,
                fb,
                ud,
                yaw,
            )
        elif target_height is not None and isHeightReached:
            drone.send_rc_control(
                lr,
                fb,
                0,          # ud
                yaw,
            )

        await asyncio.sleep(interval)

    drone.send_rc_control(
        0,
        0,
        0,
        0,
    )