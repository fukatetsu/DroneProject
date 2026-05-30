from __future__ import annotations

import asyncio
import contextlib
from typing import Optional

from ...models.imu_state import ImuState
from .input_device import InputDevice


class BleImuInput(InputDevice):
    def __init__(self) -> None:
        self._state = ImuState()
        self._task: Optional[asyncio.Task[None]] = None
        self._stop_event = asyncio.Event()

    @property
    def state(self) -> ImuState:
        return self._state

    async def start(self) -> None:
        self._stop_event.clear()
        if self._task is None or self._task.done():
            self._task = asyncio.create_task(self._run())

    async def stop(self) -> None:
        self._stop_event.set()
        if self._task is not None:
            self._task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await self._task

    async def _run(self) -> None:
        while not self._stop_event.is_set():
            self._state = await self._read_imu_state()
            await asyncio.sleep(0.02)

    async def _read_imu_state(self) -> ImuState:
        raise NotImplementedError("BLE IMU 読み取り処理を実装してください。")
