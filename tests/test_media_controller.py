import asyncio

import pytest

from src.output.camera_viewer import CameraViewer
from src.output.media_controller import MediaController


class FakeDrone:
    def __init__(self) -> None:
        self.stream_started = False
        self.stream_stopped = False

    def start_video_stream(self) -> None:
        self.stream_started = True

    def stop_video_stream(self) -> None:
        self.stream_stopped = True

    def get_video_frame(self):
        return None


class FakeCv2:
    def __init__(self) -> None:
        self.windows = []

    def namedWindow(self, title: str) -> None:
        self.windows.append(("named", title))

    def destroyWindow(self, title: str) -> None:
        self.windows.append(("destroy", title))

    def imshow(self, title: str, frame) -> None:
        self.windows.append(("imshow", title, frame))

    def waitKey(self, delay: int) -> int:
        return 0


def test_camera_viewer_start_and_stop(monkeypatch):
    fake_cv2 = FakeCv2()
    monkeypatch.setattr("src.output.camera_viewer.cv2", fake_cv2)

    drone = FakeDrone()
    viewer = CameraViewer(drone)

    viewer.start()
    assert drone.stream_started is True

    viewer.stop()
    assert drone.stream_stopped is True


def test_media_controller_enable_and_disable_camera(monkeypatch):
    monkeypatch.setattr("src.output.media_controller.CameraViewer", CameraViewer)
    monkeypatch.setattr("src.output.media_controller.cv2", FakeCv2())

    drone = FakeDrone()
    controller = MediaController(drone)

    asyncio.run(controller.enable_camera())
    assert controller.is_camera_enabled() is True
    assert controller._camera_viewer is not None

    asyncio.run(controller.disable_camera())
    assert controller.is_camera_enabled() is False


def test_media_controller_pauses_camera_viewer_for_other_content(monkeypatch):
    class TrackingCameraViewer(CameraViewer):
        def __init__(self, drone) -> None:
            super().__init__(drone)
            self.paused = False
            self.resumed = False

        def pause(self) -> None:
            self.paused = True

        def resume(self) -> None:
            self.resumed = True

    monkeypatch.setattr("src.output.media_controller.CameraViewer", TrackingCameraViewer)
    monkeypatch.setattr("src.output.media_controller.cv2", FakeCv2())

    drone = FakeDrone()
    controller = MediaController(drone)

    asyncio.run(controller.enable_camera())
    controller.show_image("title.png")
    assert controller._camera_viewer.paused is True

    controller.show_camera()
    assert controller._camera_viewer.resumed is True


def test_media_and_camera_use_same_window_title(monkeypatch):
    fake_cv2 = FakeCv2()
    monkeypatch.setattr("src.output.media_controller.cv2", fake_cv2)
    monkeypatch.setattr("src.output.camera_viewer.cv2", fake_cv2)

    drone = FakeDrone()
    controller = MediaController(drone)
    controller.show_image("title.png")
    assert controller._window_title == "Drone Media Output"

    viewer = CameraViewer(drone)
    assert viewer._window_title == "Drone Media Output"
