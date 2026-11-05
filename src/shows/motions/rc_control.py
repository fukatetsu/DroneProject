from __future__ import annotations

import asyncio
import time

from ...controllers.drone import DroneController


async def rc_control_for(
    drone: DroneController,
    command: tuple[int, int, int, int],
    *,
    duration: float,
    interval: float = 0.1,
) -> None:
    """指定したRC指令を一定時間繰り返し送信し、終了時に停止する。

    Args:
        drone: RC指令を送信するドローンコントローラー。
        command: RC指令（左右、前後、上下、回転）。
        duration: 指令を継続する時間（秒）。
        interval: 指令を再送する間隔（秒）。
    """
    if duration < 0:
        raise ValueError("duration must be non-negative")
    if interval <= 0:
        raise ValueError("interval must be positive")

    end_time = time.monotonic() + duration

    try:
        while time.monotonic() < end_time:
            drone.send_rc_control(*command)
            remaining = end_time - time.monotonic()
            await asyncio.sleep(min(interval, remaining))
    finally:
        drone.send_rc_control(0, 0, 0, 0)


async def alternate_rc_control_for(
    drone: DroneController,
    first: tuple[int, int, int, int],
    second: tuple[int, int, int, int],
    *,
    duration: float,
    interval: float = 0.1,
) -> None:
    """2つのRC指令を一定間隔で交互に送信し、指定時間後に停止する。

    Args:
        drone: RC指令を送信するドローンコントローラー。
        first: 最初に送信する指令（左右、前後、上下、回転）。
        second: 2番目に送信する指令（左右、前後、上下、回転）。
        duration: 指令を交互に送信する時間（秒）。
        interval: 指令を切り替える間隔（秒）。
    """
    if duration < 0:
        raise ValueError("duration must be non-negative")
    if interval <= 0:
        raise ValueError("interval must be positive")

    commands = (first, second)
    command_index = 0
    end_time = time.monotonic() + duration

    try:
        while time.monotonic() < end_time:
            drone.send_rc_control(*commands[command_index])
            command_index = 1 - command_index
            remaining = end_time - time.monotonic()
            await asyncio.sleep(min(interval, remaining))
    finally:
        drone.send_rc_control(0, 0, 0, 0)
