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
from src.shows.flight.bounce_show import BounceShow
from src.shows.flight.flip_forward_show import FlipForwardShow
from src.shows.flight.landing_show import LandingShow
from src.shows.flight.move_forward_show import MoveForwardShow
from src.shows.flight.rotate_180_show import Rotate180Show
from src.shows.flight.rotate_right_show import RotateRightShow
from src.shows.flight.small_square_show import SmallSquareShow
from src.shows.flight.takeoff_show import TakeoffShow
from src.shows.flight.state_monitor_show import StateMonitorShow
from src.shows.flight.align_yaw_show import AlignYawShow
from src.shows.flight.puppet_move import PuppetShow
from src.shows.flight.butterfly_escape import ButterflyEscapeShow   
from src.shows.flight.follow_pitch_show import FollowPitchShow
from src.shows.flight.arc_move_test_show import ArcMoveTestShow
from src.controllers.drone import DroneController, MockDroneController
from src.controllers.keyboard import KeyboardController
from src.shows.camera_viewer import CameraViewer
from src.analyzers import HoopAnalyzer
from src.inputs.imu.udp_imu_input import UdpImuInput

try:
    from src.controllers.drone import TelloController
except ImportError:  # pragma: no cover
    TelloController = None


def register_builtin_shows() -> None:
    registry.register("takeoff", lambda drone: TakeoffShow(drone))
    registry.register("landing", lambda drone: LandingShow(drone))
    registry.register("move_forward", lambda drone: MoveForwardShow(drone))
    registry.register("rotate_right", lambda drone: RotateRightShow(drone))
    registry.register("rotate_180", lambda drone: Rotate180Show(drone))
    registry.register("flip_forward", lambda drone: FlipForwardShow(drone))
    registry.register("small_square", lambda drone: SmallSquareShow(drone))
    registry.register("bounce", lambda drone: BounceShow(drone))
    registry.register("state_monitor", lambda drone: StateMonitorShow(drone))
    registry.register("align_yaw", lambda drone: AlignYawShow(drone))
    registry.register("butterfly_escape", lambda drone: ButterflyEscapeShow(drone))
    registry.register("follow_pitch", lambda drone: FollowPitchShow(drone))
    registry.register("puppet_move", lambda drone: PuppetShow(drone))
    registry.register("arc_move_test", lambda drone: ArcMoveTestShow(drone))

def create_show_factory(drone: DroneController) -> Callable[[str], object]:
    return lambda name: registry.create(name, drone)


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

    register_builtin_shows()
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
        base_factory = create_show_factory(drone)

        def injected_factory(name: str):
            if name == "align_yaw":
                return AlignYawShow(drone, analyzer=hoop_analyzer)
            elif name == "follow_pitch":
                return FollowPitchShow(drone, analyzer=hoop_analyzer)   
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
