from __future__ import annotations

import asyncio
import math


async def eased_move(
    drone,
    *,
    lr: int = 0,
    fb: int = 0,
    ud: int = 0,
    yaw: int = 0,
    duration: float = 1.0,
    steps: int = 20,
) -> None:
    """
    0 → 最大 → 0
    """

    for i in range(steps):
        t = i / (steps - 1)

        ease = math.sin(math.pi * t)

        drone.send_rc_control(
            int(lr * ease),
            int(fb * ease),
            int(ud * ease),
            int(yaw * ease),
        )

        await asyncio.sleep(duration / steps)

    drone.send_rc_control(0, 0, 0, 0)


async def swing_move(
    drone,
    *,
    lr: int = 0,
    fb: int = 0,
    ud: int = 0,
    yaw: int = 0,
    duration: float = 2.0,
    steps: int = 40,
) -> None:
    """
    -最大 → +最大 → -最大
    """

    for i in range(steps):
        t = i / (steps - 1)

        swing = math.sin(2 * math.pi * t)

        drone.send_rc_control(
            int(lr * swing),
            int(fb * swing),
            int(ud * swing),
            int(yaw * swing),
        )

        await asyncio.sleep(duration / steps)

    drone.send_rc_control(0, 0, 0, 0)