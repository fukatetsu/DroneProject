from __future__ import annotations

import argparse
import asyncio
import sys
import contextlib
from pathlib import Path
from typing import Callable

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from src.registry import registry
from src.runtime.scenario import Scenario
from src.runtime.scenario_runner import ScenarioRunner

import src.shows.flight
import src.shows.someji

from src.shows.base.show import Show
from src.shows.flight.align_yaw_show import AlignYawShow
from src.shows.flight.follow_pitch_show import FollowPitchShow
from src.shows.someji.s_followpitch import FollowPitchShow_s
from src.shows.someji.s_align_yaw import AlignYawShow_s
from src.shows.someji.s_kids_demo import KidsDemo_s

from src.controllers.drone import DroneController, MockDroneController
from src.controllers.keyboard import KeyboardController
from src.output.camera_viewer import CameraViewer
from src.analyzers import HoopAnalyzer
from src.inputs.imu.udp_imu_input import UdpImuInput

try:
    from src.controllers.drone import TelloController
except ImportError:  # pragma: no cover
    TelloController = None


def register_builtin_shows(enable_output: bool = False) -> None:
    for cls in Show.__subclasses__():
        def _factory(drone: DroneController, cls: type[Show] = cls, enabled: bool = enable_output):
            show_enabled = enabled or cls.use_media_output
            show = cls(drone, enable_output=show_enabled)
            if hasattr(show, "set_output_enabled"):
                show.set_output_enabled(show_enabled)
            return show

        registry.register(cls.__name__, _factory)

def create_show_factory(drone: DroneController, enable_output: bool = False) -> Callable[[str], object]:
    def _factory(name: str):
        show = registry.create(name, drone)
        if hasattr(show, "set_output_enabled"):
            show.set_output_enabled(
                enable_output or show.use_media_output
            )
        return show
    return _factory


def create_drone(use_mock: bool = False) -> DroneController:
    if use_mock:
        print("Starting with MockDroneController by request")
        return MockDroneController()

    if TelloController is None:
        print("djitellopy not installed: using MockDroneController for demo execution")
        return MockDroneController()

    try:
        return TelloController()
    except ImportError:
        print("djitellopy import failed: using MockDroneController for demo execution")
        return MockDroneController()


async def main() -> None:
    parser = argparse.ArgumentParser(description="Run demo scenario")
    parser.add_argument(
        "--scenario",
        default=str(Path(__file__).parent / "scenarios" / "demo.json"),
        help="Path to scenario JSON file",
    )
    parser.add_argument(
        "--mock",
        action="store_true",
        help="Start with MockDroneController instead of a real Tello controller.",
    )
    parser.add_argument(
        "--camera",
        action="store_true",
        help="Enable camera viewer to display video stream from drone.",
    )
    args = parser.parse_args()

    register_builtin_shows(enable_output=args.camera)
    scenario = Scenario.load_from_file(args.scenario)
    drone = create_drone(use_mock=args.mock)

    print(f"Loading scenario: {args.scenario}")
    print(f"Shows: {[step.show_name for step in scenario.steps]}")

    try:
        try:
            await drone.connect()
        except Exception as error:
            if isinstance(drone, MockDroneController):
                raise
            print(
                f"Tello connection failed: {error}\n"
                "Falling back to MockDroneController for demo execution"
            )
            drone = MockDroneController()
            await drone.connect()

        print("Drone connected. Running scenario...")

        # Start UDP IMU input and feed a HoopAnalyzer instance from it.
        hoop_analyzer = HoopAnalyzer()
        imu_input = UdpImuInput()
        await imu_input.start()

        async def _feed_analyzer() -> None:
            last_state = None
            try:
                while True:
                    imu = imu_input.state

                    # Detect change by comparing dataclass equality (frozen dataclass supports value equality)
                    if imu != last_state:
                        hoop_analyzer.update(imu)
                        last_state = imu

                    await asyncio.sleep(0.01)
            except asyncio.CancelledError:
                return

        feed_task = asyncio.create_task(_feed_analyzer())

        # Wrap show factory to inject the HoopAnalyzer into AlignYawShow explicitly.
        base_factory = create_show_factory(drone, enable_output=args.camera)

        def injected_factory(name: str):
            if name == "AlignYawShow":
                return AlignYawShow(drone, analyzer=hoop_analyzer)
            elif name == "FollowPitchShow":
                return FollowPitchShow(drone, analyzer=hoop_analyzer)   
            elif name == "FollowPitchShow_s":
                return FollowPitchShow_s(drone, analyzer=hoop_analyzer)   
            elif name =="AlignYawShow_s":
                return AlignYawShow_s(drone, analyzer=hoop_analyzer)
            elif name =="KidsDemo_s":
                return KidsDemo_s(drone, analyzer=hoop_analyzer)
            return base_factory(name)

        runner = ScenarioRunner(
            scenario=scenario,
            show_factory=injected_factory,
            on_land=drone.land,
            on_emergency=drone.emergency,
            on_pause=drone.pause,
        )

        controller = KeyboardController(runner.send_command)
        controller.start()

        # Initialize camera viewer if requested
        camera_viewer = None
        if args.camera:
            try:
                camera_viewer = CameraViewer(drone)
                camera_viewer.start()
                print("Camera viewer started.")
            except ImportError as e:
                print(f"Camera viewer not available: {e}")

        try:
            await runner.run()
        finally:
            # stop camera viewer
            if camera_viewer is not None:
                camera_viewer.stop()
            # stop feeder task and IMU input
            feed_task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await feed_task
            await imu_input.stop()
            # stop keyboard controller
            with contextlib.suppress(Exception):
                await controller.stop()
    finally:
        print("Stopping drone and disconnecting...")
        await drone.disconnect()
        print("Finished.")


if __name__ == "__main__":
    asyncio.run(main())
