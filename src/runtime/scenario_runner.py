from __future__ import annotations

import asyncio
import contextlib
from enum import Enum
from typing import Any, Awaitable, Callable, Dict, Optional, Tuple

from .scenario import Scenario, ScenarioStep


class ShowProtocol:
    async def start(self) -> None:
        raise NotImplementedError

    async def run(self) -> None:
        raise NotImplementedError

    async def stop(self) -> None:
        raise NotImplementedError


class ScenarioCommand(Enum):
    PAUSE = "pause"
    RESUME = "resume"
    NEXT_SHOW = "next_show"
    PREVIOUS_SHOW = "previous_show"
    RESTART_SHOW = "restart_show"
    JUMP_TO_SHOW = "jump_to_show"
    LAND = "land"
    EMERGENCY = "emergency"


ScenarioCommandPayload = Optional[Dict[str, Any]]
ShowFactory = Callable[[str], ShowProtocol]
Callback = Callable[[], Awaitable[None]]


class ScenarioRunner:
    def __init__(
        self,
        scenario: Scenario,
        show_factory: ShowFactory,
        on_land: Optional[Callback] = None,
        on_emergency: Optional[Callback] = None,
    ):
        self.scenario = scenario
        self.show_factory = show_factory
        self.on_land = on_land
        self.on_emergency = on_emergency
        self._command_queue: asyncio.Queue[Tuple[str, ScenarioCommandPayload]] = asyncio.Queue()
        self._paused = False
        self._running = False
        self.current_show: Optional[ShowProtocol] = None
        self._current_show_task: Optional[asyncio.Task[None]] = None

    @property
    def paused(self) -> bool:
        return self._paused

    @property
    def running(self) -> bool:
        return self._running

    async def send_command(
        self,
        command: str,
        payload: ScenarioCommandPayload = None,
    ) -> None:
        await self._command_queue.put((command, payload))

    async def run(self) -> None:
        self._running = True
        while self._running:
            step = self.scenario.current_step
            action = await self._run_step(step)
            if action == "stop":
                break
            if action == "restart":
                continue
            if action in {"previous", "jump"}:
                continue
            if self.scenario.is_last_step():
                break
            self.scenario.advance()

    async def _run_step(self, step: ScenarioStep) -> str:
        self.current_show = self.show_factory(step.show_name)
        await self.current_show.start()

        try:
            action = await self._execute_show(step)
        finally:
            await self.current_show.stop()
            self.current_show = None

        return action

    async def _execute_show(self, step: ScenarioStep) -> str:
        show_task = asyncio.create_task(self.current_show.run())
        self._current_show_task = show_task

        try:
            if step.transition.type == "manual":
                return await self._run_manual(show_task)
            if step.transition.type == "duration":
                return await self._run_with_duration(show_task, step.transition.seconds)
            return await self._run_until_finished(show_task)
        finally:
            if not show_task.done():
                show_task.cancel()
                with contextlib.suppress(asyncio.CancelledError):
                    await show_task
            self._current_show_task = None

    async def _run_until_finished(self, show_task: asyncio.Task[None]) -> str:
        while self._running and not show_task.done():
            command, payload = await self._wait_for_command_or_show(show_task)
            if command is None:
                return "advance"
            action = await self._process_command(command, payload)
            if action == "pause_wait":
                # Pause loop: wait for RESUME or other transition commands
                while self._paused and self._running:
                    command, payload = await self._wait_for_command_or_show(show_task)
                    if command is None:
                        return "advance"
                    action = await self._process_command(command, payload)
                    if action != "continue":
                        return action
                continue
            if action != "continue":
                return action
        return "advance"

    async def _run_with_duration(
        self,
        show_task: asyncio.Task[None],
        seconds: Optional[float],
    ) -> str:
        if seconds is None:
            raise ValueError("duration transition requires seconds")

        timer_task = asyncio.create_task(asyncio.sleep(seconds))
        try:
            while self._running and not show_task.done() and not timer_task.done():
                command_task = asyncio.create_task(self._command_queue.get())
                done, pending = await asyncio.wait(
                    {show_task, timer_task, command_task},
                    return_when=asyncio.FIRST_COMPLETED,
                )

                if show_task in done:
                    command_task.cancel()
                    with contextlib.suppress(asyncio.CancelledError):
                        await command_task
                    return "advance"

                if timer_task in done:
                    command_task.cancel()
                    with contextlib.suppress(asyncio.CancelledError):
                        await command_task
                    return "advance"

                if command_task in done:
                    command, payload = command_task.result()
                    action = await self._process_command(command, payload)
                    if action == "pause_wait":
                        # Pause loop during duration: timer pauses, wait for RESUME
                        timer_task.cancel()
                        with contextlib.suppress(asyncio.CancelledError):
                            await timer_task
                        while self._paused and self._running:
                            command, payload = await self._command_queue.get()
                            action = await self._process_command(command, payload)
                            if action != "continue":
                                return action
                        # Resume: restart timer
                        timer_task = asyncio.create_task(asyncio.sleep(seconds))
                        continue
                    if action != "continue":
                        return action
                    continue

                for task in pending:
                    task.cancel()
                    with contextlib.suppress(asyncio.CancelledError):
                        await task
        finally:
            timer_task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await timer_task

        return "advance"

    async def _run_manual(self, show_task: asyncio.Task[None]) -> str:
        while self._running and not show_task.done():
            command, payload = await self._wait_for_command_or_show(show_task)
            if command is None:
                return "advance"
            action = await self._process_command(command, payload)
            if action == "pause_wait":
                # Pause loop: wait for RESUME or other transition commands
                while self._paused and self._running:
                    command, payload = await self._command_queue.get()
                    action = await self._process_command(command, payload)
                    if action != "continue":
                        return action
                continue
            if action != "continue":
                return action
        return "advance"

    async def _wait_for_command_or_show(
        self,
        show_task: asyncio.Task[None],
    ) -> Tuple[Optional[str], ScenarioCommandPayload]:
        if show_task.done():
            return None, None

        command_task = asyncio.create_task(self._command_queue.get())
        done, pending = await asyncio.wait(
            {show_task, command_task},
            return_when=asyncio.FIRST_COMPLETED,
        )

        if show_task in done:
            command_task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await command_task
            return None, None

        command, payload = command_task.result()
        return command, payload

    async def _process_command(
        self,
        command: str,
        payload: ScenarioCommandPayload,
    ) -> str:
        if command == ScenarioCommand.PAUSE.value:
            self._paused = True
            return "pause_wait"

        if command == ScenarioCommand.RESUME.value:
            self._paused = False
            return "continue"

        if command == ScenarioCommand.NEXT_SHOW.value:
            self.scenario.advance()
            return "transition"

        if command == ScenarioCommand.PREVIOUS_SHOW.value:
            self.scenario.previous()
            return "previous"

        if command == ScenarioCommand.RESTART_SHOW.value:
            return "restart"

        if command == ScenarioCommand.JUMP_TO_SHOW.value:
            if isinstance(payload, dict) and "show_id" in payload:
                self.scenario.jump_to(str(payload["show_id"]))
            return "jump"

        if command == ScenarioCommand.LAND.value:
            if self.on_land is not None:
                await self.on_land()
            self._running = False
            return "stop"

        if command == ScenarioCommand.EMERGENCY.value:
            if self.on_emergency is not None:
                await self.on_emergency()
            self._running = False
            return "stop"

        return "continue"

    async def stop(self) -> None:
        self._running = False
        if self._current_show_task is not None:
            self._current_show_task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await self._current_show_task
