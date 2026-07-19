import asyncio

from src.shows.flight.demo_media_show import DemoMediaShow


class FakeDrone:
    pass


def test_demo_media_show_lifecycle(monkeypatch):
    monkeypatch.setattr("src.output.camera_viewer.CameraViewer.start", lambda self: None)
    monkeypatch.setattr("src.output.camera_viewer.CameraViewer.stop", lambda self: None)
    monkeypatch.setattr("src.output.camera_viewer.CameraViewer.update", lambda self: None)
    monkeypatch.setattr("src.output.media_controller.MediaController._display_frame", lambda self, frame: None)
    monkeypatch.setattr("src.output.media_controller.MediaController._ensure_window", lambda self: None)
    monkeypatch.setattr("src.output.media_controller.MediaController._create_black_frame", lambda self: None)

    async def run_show() -> None:
        show = DemoMediaShow(FakeDrone())
        await show.start()
        await show.run()
        await show.stop()
        assert show.media.is_camera_enabled() is False

    asyncio.run(run_show())


def test_disabled_output_does_not_create_window(monkeypatch):
    def fail_if_called(self):
        raise AssertionError("window should not be created")

    monkeypatch.setattr("src.output.media_controller.MediaController._ensure_window", fail_if_called)

    show = DemoMediaShow(FakeDrone())
    show.set_output_enabled(False)
    show.media.show_image("title.png")


def test_demo_media_show_defaults_to_enabled_output():
    show = DemoMediaShow(FakeDrone())
    assert show.media._enabled is True
