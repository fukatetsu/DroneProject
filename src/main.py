from __future__ import annotations

import argparse
import asyncio
import sys
import contextlib
from pathlib import Path
from typing import Callable, Optional

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from src.registry import registry
from src.runtime.scenario import Scenario
from src.runtime.scenario_runner import ScenarioRunner

import src.shows.rug_experiment
import src.shows.flight
import src.shows.someji
import src.shows.ISCA
import src.shows.reel
import src.shows.interaction.face_follow_show


from src.shows.base.show import Show
from src.shows.flight.align_yaw_show import AlignYawShow
from src.shows.flight.follow_pitch_show import FollowPitchShow
from src.shows.someji.s_followpitch import FollowPitchShow_s
from src.shows.someji.s_align_yaw import AlignYawShow_s
from src.shows.someji.s_kids_demo import KidsDemo_s
from src.shows.interaction.face_follow_show import FaceFollowShow

from src.controllers.drone import DroneController, MockDroneController
from src.controllers.keyboard import KeyboardController
from src.output.camera_viewer import CameraViewer
from src.analyzers import FaceTrackingAnalyzer, HoopAnalyzer
from src.inputs.imu.udp_imu_input import UdpImuInput

try:
    from src.controllers.drone import TelloController
except ImportError:  # pragma: no cover
    TelloController = None


def register_builtin_shows(
    hoop_analyzer: HoopAnalyzer,
    face_analyzer: Optional[FaceTrackingAnalyzer] = None,
    enable_output: bool = False,
    face_follow_max_speed: Optional[int] = None,
) -> None:

    for cls in Show.__subclasses__():

        def _factory(
            drone: DroneController,
            cls: type[Show] = cls,
        ):

            kwargs = {}

            if cls.requires_analyzer:
                kwargs["analyzer"] = hoop_analyzer
            elif getattr(cls, "requires_face_analyzer", False):
                kwargs["analyzer"] = face_analyzer or FaceTrackingAnalyzer()
                if face_follow_max_speed is not None:
                    kwargs["max_speed"] = face_follow_max_speed

            show_enabled = (
                enable_output
                or cls.use_media_output
            )

            show = cls(
                drone,
                enable_output=show_enabled,
                **kwargs,
            )

            return show

        registry.register(
            cls.__name__,
            _factory,
        )




def create_drone(
    use_mock: bool = False,
    require_real: bool = False,
) -> DroneController:
    if use_mock:
        print("Starting with MockDroneController by request")
        return MockDroneController()

    if TelloController is None:
        if require_real:
            raise RuntimeError("--real requires djitellopy and a Tello controller")
        print("djitellopy not installed: using MockDroneController for demo execution")
        return MockDroneController()

    try:
        return TelloController()
    except ImportError:
        if require_real:
            raise
        print("djitellopy import failed: using MockDroneController for demo execution")
        return MockDroneController()


async def main() -> None:
    parser = argparse.ArgumentParser(description="Run demo scenario")
    parser.add_argument(
        "--scenario",
        default=str(Path(__file__).parent / "scenarios" / "demo.json"),
        help="Path to scenario JSON file",
    )
    connection_mode = parser.add_mutually_exclusive_group()
    connection_mode.add_argument(
        "--mock",
        action="store_true",
        help="Start with MockDroneController instead of a real Tello controller.",
    )
    connection_mode.add_argument(
        "--real",
        action="store_true",
        help="Require a real Tello controller; never fall back to MockDroneController.",
    )
    parser.add_argument(
        "--camera",
        action="store_true",
        help="Enable media output.",
    )
    args = parser.parse_args()

    scenario = Scenario.load_from_file(args.scenario)
    drone = create_drone(use_mock=args.mock, require_real=args.real)

    print(f"Loading scenario: {args.scenario}")
    print(f"Shows: {[step.show_name for step in scenario.steps]}")

    try:
        try:
            await drone.connect()
        except Exception as error:
            if isinstance(drone, MockDroneController) or args.real:
                if args.real:
                    raise RuntimeError(f"Unable to connect to the required Tello drone: {error}") from error
                raise

            print(
                f"Tello connection failed: {error}\n"
                "Falling back to MockDroneController for demo execution"
            )

            drone = MockDroneController()
            await drone.connect()

        print("Drone connected. Running scenario...")

        # --------------------------------------------
        # Hoop analyzer
        # --------------------------------------------

        hoop_analyzer = HoopAnalyzer()

        imu_input = UdpImuInput()
        await imu_input.start()

        async def _feed_analyzer() -> None:

            last_state = None

            try:
                while True:

                    imu = imu_input.state

                    if imu != last_state:
                        hoop_analyzer.update(imu)
                        last_state = imu

                    await asyncio.sleep(0.01)

            except asyncio.CancelledError:
                return

        feed_task = asyncio.create_task(
            _feed_analyzer()
        )

        # --------------------------------------------
        # Register shows
        # --------------------------------------------

        register_builtin_shows(
            hoop_analyzer=hoop_analyzer,
            face_analyzer=FaceTrackingAnalyzer(),
            enable_output=args.camera,
            # 実機モードのRC上限。調整の考え方はdocs/technical/system/face_follow_tuning.mdを参照。
            face_follow_max_speed=70 if args.real else None,
        )

        # --------------------------------------------
        # Runner
        # --------------------------------------------

        runner = ScenarioRunner(
            scenario=scenario,
            show_factory=lambda name: registry.create(name, drone),
            on_land=drone.land,
            on_emergency=drone.emergency,
            on_pause=drone.pause,
        )

        controller = KeyboardController(
            runner.send_command
        )

        controller.start()

        try:
            await runner.run()

        finally:

            feed_task.cancel()

            with contextlib.suppress(asyncio.CancelledError):
                await feed_task

            await imu_input.stop()

            with contextlib.suppress(Exception):
                await controller.stop()

    finally:

        print("Stopping drone and disconnecting...")

        await drone.disconnect()

        print("Finished.")


if __name__ == "__main__":
    asyncio.run(main())
