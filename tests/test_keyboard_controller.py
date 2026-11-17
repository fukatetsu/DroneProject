import asyncio

from src.controllers.keyboard import KeyboardCommand, KeyboardController
from src.runtime.scenario import Scenario, ScenarioStep, Transition
from src.runtime.scenario_runner import ScenarioRunner
from src.shows.base.show import Show


def test_keyboard_controller_routes_control_keys_and_show_keys():
    async def run_test():
        commands = []
        show_keys = []

        async def send_command(command, payload=None):
            commands.append((command, payload))

        async def send_key_event(key):
            show_keys.append(key)

        controller = KeyboardController(send_command, send_key_event)
        await controller._handle_key("p")
        await controller._handle_key("UP")
        await controller._handle_key("e")

        assert commands == [
            (KeyboardCommand.PAUSE.value, None),
            (KeyboardCommand.EMERGENCY.value, None),
        ]
        assert show_keys == ["UP"]

    asyncio.run(run_test())


def test_keyboard_controller_supports_all_scenario_commands():
    async def run_test():
        commands = []

        async def send_command(command, payload=None):
            commands.append((command, payload))

        controller = KeyboardController(send_command)
        for key in ("p", "r", "n", "b", "t", "l", "e"):
            await controller._handle_key(key)

        await controller._handle_key("j")
        for key in ("s", "h", "o", "w", "-", "2", "\r"):
            await controller._handle_key(key)

        assert commands == [
            (KeyboardCommand.PAUSE.value, None),
            (KeyboardCommand.RESUME.value, None),
            (KeyboardCommand.NEXT_SHOW.value, None),
            (KeyboardCommand.PREVIOUS_SHOW.value, None),
            (KeyboardCommand.RESTART_SHOW.value, None),
            (KeyboardCommand.LAND.value, None),
            (KeyboardCommand.EMERGENCY.value, None),
            (KeyboardCommand.JUMP_TO_SHOW.value, {"show_id": "show-2"}),
        ]

    asyncio.run(run_test())


def test_show_handle_key_runs_only_registered_async_events():
    class TestShow(Show):
        async def start(self):
            pass

        async def run(self):
            pass

        async def stop(self):
            pass

    async def run_test():
        called = []
        show = object.__new__(TestShow)

        async def move_forward():
            called.append("forward")

        show.key_events = {"UP": move_forward}
        await show.handle_key("up")
        await show.handle_key("UNKNOWN")

        assert called == ["forward"]

    asyncio.run(run_test())


def test_runner_routes_key_event_to_current_show_only():
    async def run_test():
        class FakeShow:
            def __init__(self):
                self.received_keys = []

            async def handle_key(self, key):
                self.received_keys.append(key)

        first_show = FakeShow()
        second_show = FakeShow()
        scenario = Scenario(
            [
                ScenarioStep(
                    id="first",
                    comment=None,
                    show_name="First",
                    transition=Transition(type="auto"),
                )
            ]
        )
        def create_show(name):
            if name != "First":
                raise AssertionError(f"Unexpected show: {name}")
            return first_show

        runner = ScenarioRunner(scenario, create_show)
        runner.current_show = first_show

        await runner.send_key_event("UP")
        command, payload = await runner._command_queue.get()
        runner.current_show = second_show
        await runner._process_command(command, payload)

        assert first_show.received_keys == []
        assert second_show.received_keys == []

        await runner.send_key_event("DOWN")
        command, payload = await runner._command_queue.get()
        await runner._process_command(command, payload)

        assert first_show.received_keys == []
        assert second_show.received_keys == ["DOWN"]

        await runner.send_command("show_key", {"key": "LEFT"})
        command, payload = await runner._command_queue.get()
        await runner._process_command(command, payload)

        assert second_show.received_keys == ["DOWN", "LEFT"]

    asyncio.run(run_test())
