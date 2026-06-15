from __future__ import annotations

import asyncio
import contextlib
from typing import Any, Awaitable, Callable, Optional

from . import KeyboardCommand


class KeyboardController:
    """Simple keyboard controller using stdin lines.

    This is a minimal implementation for operator testing and local
    development. It reads lines from stdin (via a thread executor) and
    maps them to `KeyboardCommand` values, then forwards to the provided
    `send_command` coroutine function.

    Usage:
        controller = KeyboardController(scenario_runner.send_command)
        controller.start()

    Stop with `await controller.stop()`.
    """

    def __init__(self, send_command: Callable[[str, Optional[dict]], Awaitable[None]]):
        self._send_command = send_command
        self._task: Optional[asyncio.Task[Any]] = None
        self._running = False

    def start(self) -> None:
        if self._running:
            return
        self._running = True
        self._task = asyncio.create_task(self._input_loop())

    async def stop(self) -> None:
        self._running = False
        if self._task is not None:
            self._task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await self._task

    async def _input_loop(self) -> None:
        loop = asyncio.get_event_loop()
        while self._running:
            try:
                line = await loop.run_in_executor(None, input, "> ")
            except Exception:
                break

            cmd = (line or "").strip()
            if not cmd:
                continue

            parts = cmd.split()
            key = parts[0].lower()

            # Map simple keywords to commands
            if key in {"p", "pause"}:
                await self._send_command(KeyboardCommand.PAUSE.value)
                print("sent: pause")
                continue

            if key in {"r", "resume"}:
                await self._send_command(KeyboardCommand.RESUME.value)
                print("sent: resume")
                continue

            if key in {"n", "next"}:
                await self._send_command(KeyboardCommand.NEXT_SHOW.value)
                print("sent: next_show")
                continue

            if key in {"b", "prev", "previous"}:
                await self._send_command(KeyboardCommand.PREVIOUS_SHOW.value)
                print("sent: previous_show")
                continue

            if key in {"restart"}:
                await self._send_command(KeyboardCommand.RESTART_SHOW.value)
                print("sent: restart_show")
                continue

            if key in {"jump"} and len(parts) >= 2:
                show_id = parts[1]
                await self._send_command(KeyboardCommand.JUMP_TO_SHOW.value, {"show_id": show_id})
                print(f"sent: jump_to_show {show_id}")
                continue

            if key in {"land"}:
                await self._send_command(KeyboardCommand.LAND.value)
                print("sent: land")
                continue

            if key in {"emergency", "exit", "quit"}:
                await self._send_command(KeyboardCommand.EMERGENCY.value)
                print("sent: emergency")
                # after emergency we break loop
                break

            print(f"unknown command: {cmd}")

