import asyncio
import random
import time

import numpy as np
import pytest

from src.analyzers.face_tracking_analyzer import FaceTrackingAnalyzer, VideoFrameUnavailable
from src.controllers.drone.mock_controller import MockDroneController
from src.controllers.drone.tello_controller import TelloController
from src.models.hoop_state import HoopState
from src.models.face_state import FaceDetection, FaceTrackingState
from src.output.camera_viewer import CameraViewer
from src.output.media_controller import MediaController
from src.registry.show_registry import ShowRegistry
from src.runtime.scenario import Scenario, ScenarioStep, Transition
from src.runtime.scenario_runner import ScenarioCommand, ScenarioRunner
from src.shows.interaction.face_follow_show import FaceFollowShow


async def _skip_initial_height_adjustment(
    drone: object,
    target_height: int,
    max_speed: int,
) -> None:
    assert drone is not None
    assert target_height > 0
    assert max_speed > 0
from src.shows.interaction import face_follow_show as face_follow_module


def test_face_geometry_and_tracking_id_lifetime():
    boxes = [(20, 10, 30, 40, 0.9)]
    analyzer = FaceTrackingAnalyzer(detector=lambda frame: boxes, max_missed_frames=1)
    frame = np.zeros((100, 120, 3), dtype=np.uint8)

    first = analyzer.analyze(frame, captured_at=1.0, now=1.0).detections[0]
    moved = analyzer.analyze(frame, captured_at=2.0, now=2.0).detections[0]
    assert first.track_id == moved.track_id
    assert moved.center == (35.0, 30.0)
    assert moved.area == 1200
    assert moved.confidence == 0.9

    boxes.clear()
    analyzer.analyze(frame, captured_at=3.0, now=3.0)
    analyzer.analyze(frame, captured_at=4.0, now=4.0)
    boxes.append((20, 10, 30, 40, 0.9))
    reassigned = analyzer.analyze(frame, captured_at=5.0, now=5.0).detections[0]
    assert reassigned.track_id != first.track_id


def test_analyzer_distinguishes_missing_and_stale_frames():
    analyzer = FaceTrackingAnalyzer(detector=lambda frame: ())
    frame = np.zeros((24, 32, 3), dtype=np.uint8)

    with pytest.raises(VideoFrameUnavailable, match="No video frame"):
        analyzer.analyze(None, now=2.0)
    with pytest.raises(VideoFrameUnavailable, match="stale"):
        analyzer.analyze(frame, captured_at=1.0, now=2.0)

    result = analyzer.analyze(frame, captured_at=2.0, now=2.0)
    assert result.detections == ()
    assert (result.frame_width, result.frame_height) == (32, 24)


def test_default_opencv_detector_initializes_and_returns_empty_state():
    analyzer = FaceTrackingAnalyzer()
    result = analyzer.analyze(
        np.zeros((64, 64, 3), dtype=np.uint8),
        now=1.0,
    )
    assert result.detections == ()


def test_tello_capture_preserves_sdk_rgb_channel_order():
    async def verify_frame_format():
        rgb_frame = np.array([[[255, 0, 0], [0, 0, 255]]], dtype=np.uint8)
        controller = TelloController.__new__(TelloController)
        controller._tello = type(
            "FakeTello",
            (),
            {"get_frame_read": lambda self: type("FrameRead", (), {"frame": rgb_frame})()},
        )()
        controller._latest_frame = None
        controller._latest_frame_captured_at = None

        capture_task = asyncio.create_task(controller._capture_frames())
        captured_frame = None
        try:
            for _ in range(10):
                if controller._latest_frame is not None:
                    captured_frame = controller._latest_frame.copy()
                    break
                await asyncio.sleep(0.01)
        finally:
            capture_task.cancel()
            await capture_task

        assert captured_frame is not None
        assert np.array_equal(captured_frame, rgb_frame)

    asyncio.run(verify_frame_format())


def test_face_follow_scenario_is_loadable():
    scenario = Scenario.load_from_file("src/scenarios/face_follow_mock.json")
    assert scenario.current_step.show_name == "FaceFollowShow"
    assert scenario.current_step.transition.type == "manual"


def test_real_face_follow_test_scenario_has_bounded_flight_and_landing():
    scenario = Scenario.load_from_file("src/scenarios/face_follow_tello_test.json")
    assert [step.show_name for step in scenario.steps] == [
        "TakeoffShow",
        "FaceFollowShow",
        "LandingShow",
    ]
    assert scenario.steps[1].transition.type == "duration"
    assert scenario.steps[1].transition.seconds == 30


def test_require_real_never_falls_back_to_mock(monkeypatch):
    import src.main as main_module

    monkeypatch.setattr(main_module, "TelloController", None)
    with pytest.raises(RuntimeError, match="--real requires djitellopy"):
        main_module.create_drone(require_real=True)


def test_mock_stream_stays_active_until_all_users_stop():
    async def verify_shared_stream():
        drone = MockDroneController()
        frame = np.zeros((8, 8, 3), dtype=np.uint8)
        drone.set_video_frame(frame)
        first_owner = object()
        second_owner = object()

        drone.acquire_video_stream(first_owner)
        drone.acquire_video_stream(first_owner)
        drone.acquire_video_stream(second_owner)
        assert drone._video_stream_active is True

        drone.release_video_stream(first_owner)
        assert drone._video_stream_active is True
        assert drone.get_video_frame() is frame

        drone.release_video_stream(second_owner)
        await asyncio.sleep(0)
        assert drone._video_stream_active is False
        assert drone.get_video_frame() is None

    asyncio.run(verify_shared_stream())


def test_camera_viewer_and_face_follow_share_mock_stream(monkeypatch):
    monkeypatch.setattr(MediaController, "show_camera", lambda media: None)
    monkeypatch.setattr(MediaController, "show_black", lambda media: None)
    monkeypatch.setattr(
        face_follow_module,
        "adjust_height",
        _skip_initial_height_adjustment,
    )

    async def verify_shared_stream():
        drone = MockDroneController()
        drone.set_video_frame(np.zeros((8, 8, 3), dtype=np.uint8))
        viewer = CameraViewer(drone)
        show = FaceFollowShow(
            drone,
            analyzer=FaceTrackingAnalyzer(detector=lambda frame: ()),
        )

        viewer.start()
        await show.start()
        viewer.stop()
        assert drone._video_stream_active is True

        await show.stop()
        assert drone._video_stream_active is False

    asyncio.run(verify_shared_stream())


def test_face_follow_displays_annotated_camera_frame(monkeypatch):
    calls = []
    overlay_text = []
    put_text = face_follow_module.cv2.putText

    def record_text(frame, text, *args, **kwargs):
        overlay_text.append(text)
        return put_text(frame, text, *args, **kwargs)

    monkeypatch.setattr(face_follow_module.cv2, "putText", record_text)
    monkeypatch.setattr(
        face_follow_module,
        "adjust_height",
        _skip_initial_height_adjustment,
    )

    async def enable_camera(media):
        calls.append("enable")
        media._camera_enabled = True

    async def disable_camera(media):
        calls.append("disable")
        media._camera_enabled = False

    monkeypatch.setattr(MediaController, "enable_camera", enable_camera)
    monkeypatch.setattr(MediaController, "disable_camera", disable_camera)
    monkeypatch.setattr(MediaController, "show_camera", lambda media: calls.append("show"))

    async def verify_display():
        drone = MockDroneController()
        show = FaceFollowShow(
            drone,
            analyzer=FaceTrackingAnalyzer(detector=lambda frame: ()),
        )
        await show.start()
        show._latest_tracking_state = FaceTrackingState(
            detections=(FaceDetection(3, 10, 10, 30, 30),),
            frame_width=64,
            frame_height=64,
            captured_at=1.0,
        )
        show._target_id = 3

        frame = np.zeros((64, 64, 3), dtype=np.uint8)
        annotated = show._annotate_frame(frame)
        assert annotated is not frame
        assert np.any(annotated != frame)
        assert not np.any(frame)
        assert "Arrows: up/down altitude, left/right yaw" in overlay_text
        assert "Target keys: 1=Target 3" in overlay_text
        assert "1: Target 3" in overlay_text
        assert show.media._enabled is True
        assert calls == ["enable", "show"]

        await show.stop()
        assert calls[-1] == "disable"

    asyncio.run(verify_display())


def test_face_follow_manual_controls_are_serialized_with_tracking_and_select_target():
    class RecordingDrone:
        def __init__(self):
            self.commands = []

        def send_rc_control(self, left_right, forward_back, up_down, yaw):
            self.commands.append((left_right, forward_back, up_down, yaw))

    async def verify_controls():
        drone = RecordingDrone()
        show = FaceFollowShow(
            drone,
            analyzer=FaceTrackingAnalyzer(detector=lambda frame: ()),
            max_speed=45,
        )
        faces = (
            FaceDetection(1, 0, 0, 20, 20),
            FaceDetection(2, 40, 40, 30, 30),
            FaceDetection(3, 80, 80, 10, 10),
        )
        state = FaceTrackingState(faces, 100, 100, 1.0)
        show._latest_tracking_state = state

        await show.handle_key("2")
        assert show._target_id == 1
        await show.handle_key("UP")
        assert drone.commands == []

        now = time.monotonic()
        show._send_current_command(faces[0], state, now)
        assert drone.commands == [(0, 0, 45, 0)]

        show._send_current_command(faces[0], state, now + 1)
        assert drone.commands == [(0, 0, 45, 0), (0, 0, 20, -45)]

        await show.handle_key("DOWN")
        now = time.monotonic()
        show._send_current_command(faces[0], state, now)
        assert drone.commands[-1] == (0, 0, -45, 0)

        await show.handle_key("LEFT")
        now = time.monotonic()
        show._send_current_command(faces[0], state, now)
        assert drone.commands[-1] == (0, 0, 0, -45)

        await show.handle_key("RIGHT")
        now = time.monotonic()
        show._send_current_command(faces[0], state, now)
        assert drone.commands[-1] == (0, 0, 0, 45)

    asyncio.run(verify_controls())


def test_face_follow_is_registered_with_its_analyzer(monkeypatch):
    import src.main as main_module

    registry = ShowRegistry()
    analyzer = FaceTrackingAnalyzer(detector=lambda frame: ())
    monkeypatch.setattr(main_module, "registry", registry)
    main_module.register_builtin_shows(
        hoop_analyzer=object(),
        face_analyzer=analyzer,
        face_follow_max_speed=15,
    )

    show = registry.create("FaceFollowShow", object())
    assert isinstance(show, FaceFollowShow)
    assert show._analyzer is analyzer
    assert show.max_speed == 15
    assert show.media._enabled is True


class FirstChoice:
    def choice(self, values):
        return values[0]


def test_target_selection_caps_candidates_and_avoids_same_face_on_switch():
    show = FaceFollowShow(
        object(),
        analyzer=FaceTrackingAnalyzer(detector=lambda frame: ()),
        target_switch_interval=15,
        rng=FirstChoice(),
    )
    faces = tuple(
        FaceDetection(index, index * 10, 0, 100 - index, 100 - index)
        for index in range(1, 5)
    )
    state = FaceTrackingState(faces, 200, 200, 1.0)

    initial = show._select_target(state, 1.0)
    assert initial is not None
    assert initial.track_id in {1, 2, 3}
    previous_id = initial.track_id

    switched = show._select_target(state, 16.0)
    assert switched is not None
    assert switched.track_id in {1, 2, 3}
    assert switched.track_id != previous_id


def test_vertical_target_biases_lower_and_yaw_is_more_responsive():
    class RecordingDrone:
        def __init__(self):
            self.command = None

        def send_rc_control(self, left_right, forward_back, up_down, yaw):
            self.command = (left_right, forward_back, up_down, yaw)

    drone = RecordingDrone()
    show = FaceFollowShow(
        drone,
        analyzer=FaceTrackingAnalyzer(detector=lambda frame: ()),
        max_speed=100,
        yaw_gain=100,
        vertical_target_ratio=0.4,
    )
    centered_face = FaceDetection(track_id=1, x=60, y=30, width=20, height=20)
    state = FaceTrackingState(
        (centered_face,),
        frame_width=100,
        frame_height=100,
        captured_at=1.0,
    )

    show._send_tracking_command(centered_face, state)

    assert drone.command == (0, 0, 0, 40)
    assert show._control_value(0.2, show.yaw_gain) > show._control_value(0.2, show.gain)
    show._send_tracking_command(
        FaceDetection(track_id=2, x=40, y=40, width=20, height=20),
        state,
    )
    assert drone.command[2] == -10
    show._send_tracking_command(
        FaceDetection(track_id=3, x=40, y=20, width=20, height=20),
        state,
    )
    assert drone.command[2] > 0


def test_face_follow_horizontal_target_ratio_controls_yaw_alignment():
    class RecordingDrone:
        def __init__(self):
            self.command = None

        def send_rc_control(self, left_right, forward_back, up_down, yaw):
            self.command = (left_right, forward_back, up_down, yaw)

    drone = RecordingDrone()
    show = FaceFollowShow(
        drone,
        analyzer=FaceTrackingAnalyzer(detector=lambda frame: ()),
        max_speed=100,
        horizontal_target_ratio=0.6,
    )
    face = FaceDetection(track_id=1, x=40, y=40, width=20, height=20)
    state = FaceTrackingState((face,), frame_width=100, frame_height=100, captured_at=1.0)

    show._send_tracking_command(face, state)

    assert drone.command == (0, 0, 0, -6)


def test_mock_face_follow_sends_limited_rc_and_stops_without_camera(monkeypatch):
    commands = []
    result = {}
    monkeypatch.setattr(MediaController, "show_camera", lambda media: None)
    monkeypatch.setattr(MediaController, "show_black", lambda media: None)
    monkeypatch.setattr(
        face_follow_module,
        "adjust_height",
        _skip_initial_height_adjustment,
    )

    async def run_show():
        drone = MockDroneController()
        frame = np.zeros((100, 100, 3), dtype=np.uint8)
        drone.set_video_frame(frame)
        analyzer = FaceTrackingAnalyzer(
            detector=lambda image: [(80, 80, 20, 20, 1.0)]
        )
        show = FaceFollowShow(
            drone,
            analyzer=analyzer,
            poll_interval=0.005,
            rng=random.Random(0),
            gain=1000,
            max_speed=25,
        )
        original_send = drone.send_rc_control

        def record_command(left_right, forward_back, up_down, yaw):
            commands.append((left_right, forward_back, up_down, yaw))
            original_send(left_right, forward_back, up_down, yaw)

        monkeypatch.setattr(drone, "send_rc_control", record_command)
        await show.start()
        task = asyncio.create_task(show.run())
        await asyncio.sleep(0.03)
        task.cancel()
        with pytest.raises(asyncio.CancelledError):
            await task
        await show.stop()
        result["drone"] = drone

    asyncio.run(run_show())
    drone = result["drone"]

    assert commands
    assert any(command[2] == -25 and command[3] == 24 for command in commands)
    assert commands[-1] == (0, 0, 0, 0)
    assert drone.state.speed_z == 0
    assert drone._video_capture is None
    assert drone._video_stream_active is False


def test_face_follow_stops_after_video_failure_timeout(monkeypatch):
    commands = []
    monkeypatch.setattr(MediaController, "show_camera", lambda media: None)
    monkeypatch.setattr(MediaController, "show_black", lambda media: None)
    monkeypatch.setattr(
        face_follow_module,
        "adjust_height",
        _skip_initial_height_adjustment,
    )

    async def run_show():
        drone = MockDroneController()
        monkeypatch.setattr(drone, "start_video_stream", lambda: None)
        show = FaceFollowShow(
            drone,
            analyzer=FaceTrackingAnalyzer(detector=lambda frame: ()),
            poll_interval=0.005,
            frame_failure_timeout=0.015,
        )
        monkeypatch.setattr(
            drone,
            "send_rc_control",
            lambda left_right, forward_back, up_down, yaw: commands.append(
                (left_right, forward_back, up_down, yaw)
            ),
        )
        await show.start()
        with pytest.raises(RuntimeError, match="video input failed"):
            await show.run()
        await show.stop()

    asyncio.run(run_show())
    assert commands
    assert set(commands) == {(0, 0, 0, 0)}


def test_land_cancels_face_follow_before_running_callback(monkeypatch):
    monkeypatch.setattr(MediaController, "show_camera", lambda media: None)
    monkeypatch.setattr(MediaController, "show_black", lambda media: None)
    monkeypatch.setattr(
        face_follow_module,
        "adjust_height",
        _skip_initial_height_adjustment,
    )

    async def run_scenario():
        drone = MockDroneController()
        drone.set_video_frame(np.zeros((100, 100, 3), dtype=np.uint8))
        commands = []
        original_send = drone.send_rc_control

        def record_command(left_right, forward_back, up_down, yaw):
            commands.append((left_right, forward_back, up_down, yaw))
            original_send(left_right, forward_back, up_down, yaw)

        monkeypatch.setattr(drone, "send_rc_control", record_command)
        analyzer = FaceTrackingAnalyzer(
            detector=lambda frame: [(80, 80, 20, 20, 1.0)]
        )
        scenario = Scenario(
            [
                ScenarioStep(
                    id="face-follow",
                    comment=None,
                    show_name="FaceFollowShow",
                    transition=Transition(type="manual"),
                )
            ]
        )
        callback_counts = []

        async def land():
            moving_count = sum(command != (0, 0, 0, 0) for command in commands)
            await asyncio.sleep(0.02)
            callback_counts.append(
                sum(command != (0, 0, 0, 0) for command in commands) - moving_count
            )
            await drone.land()

        runner = ScenarioRunner(
            scenario=scenario,
            show_factory=lambda name: FaceFollowShow(
                drone,
                analyzer=analyzer,
                poll_interval=0.002,
            ),
            on_land=land,
        )
        task = asyncio.create_task(runner.run())
        await asyncio.sleep(0.02)
        await runner.send_command(ScenarioCommand.LAND.value)
        await task

        assert callback_counts == [0]
        assert commands[-1] == (0, 0, 0, 0)
        assert drone._video_stream_active is False

    asyncio.run(run_scenario())
