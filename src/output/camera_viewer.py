from __future__ import annotations

from typing import Any

try:
    import cv2
except ImportError:  # pragma: no cover - OpenCV is optional for non-camera output
    cv2 = None

from ..controllers.drone.drone_controller import DroneController


class CameraViewer:
    """Provide frames from the drone camera.

    This class only manages the drone video stream.
    Rendering is handled by MediaController.
    """

    def __init__(self, drone: DroneController) -> None:
        self._drone = drone
        self._running = False
        self._paused = False
        self._stream_acquired = False
        self._window_title = "Drone Media Output"

    def start(self) -> None:
        """Start the drone camera stream."""
        if self._running:
            return

        self._acquire_stream()
        self._running = True
        self._paused = False

        print("[CameraViewer] start")

    def update(self) -> Any:
        """Return the latest frame; retained for callers using the old viewer API."""
        return self.get_frame()

    def get_frame(self) -> Any:
        """Get the latest camera frame.

        Returns:
            Image frame from drone camera, or None if unavailable.
        """
        if not self._running or self._paused:
            return None

        try:
            return self._drone.get_video_frame()
        except Exception as exc:
            print(f"[CameraViewer] Error getting frame: {exc}")
            return None

    def pause(self) -> None:
        if not self._running or self._paused:
            return
        self._release_stream()
        self._paused = True

    def resume(self) -> None:
        if not self._running or not self._paused:
            return
        self._acquire_stream()
        self._paused = False

    def stop(self) -> None:
        """Stop the drone camera stream."""
        if not self._running:
            return

        self._running = False

        try:
            self._release_stream()
        except Exception as exc:
            print(f"[CameraViewer] Error stopping stream: {exc}")

        print("[CameraViewer] stop")

    def is_running(self) -> bool:
        """Return whether camera stream is active."""
        return self._running

    def _acquire_stream(self) -> None:
        if self._stream_acquired:
            return
        acquire = getattr(self._drone, "acquire_video_stream", None)
        if acquire is None:
            self._drone.start_video_stream()
        else:
            acquire(self)
        self._stream_acquired = True

    def _release_stream(self) -> None:
        if not self._stream_acquired:
            return
        release = getattr(self._drone, "release_video_stream", None)
        if release is None:
            self._drone.stop_video_stream()
        else:
            release(self)
        self._stream_acquired = False