from __future__ import annotations

import asyncio
import contextlib
import platform
import sys
from typing import Any, Awaitable, Callable, Dict, Optional

from . import KeyboardCommand


class KeyboardController:
    """Read individual console key presses and forward operator actions."""

    _COMMAND_KEYS: Dict[str, KeyboardCommand] = {
        "P": KeyboardCommand.PAUSE,
        "R": KeyboardCommand.RESUME,
        "N": KeyboardCommand.NEXT_SHOW,
        "B": KeyboardCommand.PREVIOUS_SHOW,
        "T": KeyboardCommand.RESTART_SHOW,
        "L": KeyboardCommand.LAND,
        "E": KeyboardCommand.EMERGENCY,
    }

    def __init__(
        self,
        send_command: Callable[[str, Optional[dict]], Awaitable[None]],
        send_key_event: Optional[Callable[[str], Awaitable[None]]] = None,
    ) -> None:
        self._send_command = send_command
        self._send_key_event = send_key_event
        self._task: Optional[asyncio.Task[Any]] = None
        self._running = False
        self._jump_buffer: Optional[str] = None

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
            self._task = None

    async def _input_loop(self) -> None:
        if not sys.stdin.isatty():
            print("Keyboard input requires an interactive console.")
            return

        print(
            "Keyboard: P pause, R resume, N next, B previous, T restart, "
            "J jump, L land, E emergency."
        )
        if platform.system() == "Windows":
            await self._windows_input_loop()
        else:
            await self._posix_input_loop()

    async def _windows_input_loop(self) -> None:
        import msvcrt

        arrow_keys = {"H": "UP", "P": "DOWN", "K": "LEFT", "M": "RIGHT"}
        while self._running:
            if not msvcrt.kbhit():
                await asyncio.sleep(0.01)
                continue

            key = msvcrt.getwch()
            if key in {"\x00", "\xe0"}:
                while self._running and not msvcrt.kbhit():
                    await asyncio.sleep(0.001)
                if not self._running:
                    break
                key = arrow_keys.get(msvcrt.getwch())
                if key is not None:
                    await self._handle_key(key)
                continue

            await self._handle_key(key)

    async def _posix_input_loop(self) -> None:
        import select
        import termios
        import tty

        stream = sys.stdin
        file_descriptor = stream.fileno()
        previous_settings = termios.tcgetattr(file_descriptor)
        tty.setcbreak(file_descriptor)
        try:
            while self._running:
                readable, _, _ = select.select([stream], [], [], 0)
                if not readable:
                    await asyncio.sleep(0.01)
                    continue

                key = stream.read(1)
                if key == "\x1b":
                    key = await self._read_posix_escape_sequence(stream, select)
                    if key is None:
                        continue
                await self._handle_key(key)
        finally:
            termios.tcsetattr(file_descriptor, termios.TCSADRAIN, previous_settings)

    async def _read_posix_escape_sequence(self, stream: Any, select: Any) -> Optional[str]:
        for expected in ("[",):
            deadline = asyncio.get_running_loop().time() + 0.05
            while self._running and asyncio.get_running_loop().time() < deadline:
                readable, _, _ = select.select([stream], [], [], 0)
                if readable:
                    if stream.read(1) != expected:
                        return None
                    break
                await asyncio.sleep(0.001)
            else:
                return None

        deadline = asyncio.get_running_loop().time() + 0.05
        while self._running and asyncio.get_running_loop().time() < deadline:
            readable, _, _ = select.select([stream], [], [], 0)
            if readable:
                return {
                    "A": "UP",
                    "B": "DOWN",
                    "D": "LEFT",
                    "C": "RIGHT",
                }.get(stream.read(1))
            await asyncio.sleep(0.001)
        return None

    async def _handle_key(self, key: str) -> None:
        if self._jump_buffer is not None:
            if key in {"\r", "\n"}:
                show_id = self._jump_buffer.strip()
                self._jump_buffer = None
                if show_id:
                    await self._send_command(
                        KeyboardCommand.JUMP_TO_SHOW.value,
                        {"show_id": show_id},
                    )
                    print(f"\nsent: jump_to_show {show_id}")
                else:
                    print("\njump cancelled")
            elif key == "\x1b":
                self._jump_buffer = None
                print("\njump cancelled")
            elif key in {"\b", "\x7f"}:
                self._jump_buffer = self._jump_buffer[:-1]
                print("\b \b", end="", flush=True)
            elif len(key) == 1 and key.isprintable():
                self._jump_buffer += key
                print(key, end="", flush=True)
            return

        normalized_key = key.upper()
        command = self._COMMAND_KEYS.get(normalized_key)
        if command is not None:
            await self._send_command(command.value)
            print(f"sent: {command.value}")
            if command is KeyboardCommand.EMERGENCY:
                self._running = False
            return

        if normalized_key == "J":
            self._jump_buffer = ""
            print("jump to show id: ", end="", flush=True)
            return

        if normalized_key in {"\r", "\n", "\t", "\b", "\x7f", "\x1b"}:
            return

        if self._send_key_event is not None:
            await self._send_key_event(normalized_key)
        else:
            await self._send_command("show_key", {"key": normalized_key})
