from __future__ import annotations

from typing import Any

from ..controllers.drone.drone_controller import DroneController


class CameraViewer:
    """Provide frames from the drone camera.

    This class only manages the drone video stream.
    Rendering is handled by MediaController.
    """

    def __init__(self, drone: DroneController) -> None:
        self._drone = drone
        self._running = False

    def start(self) -> None:
        """Start the drone camera stream."""
        if self._running:
            return

        self._drone.start_video_stream()
        self._running = True

        print("[CameraViewer] start")

    def get_frame(self) -> Any:
        """Get the latest camera frame.

        Returns:
            Image frame from drone camera, or None if unavailable.
        """
        if not self._running:
            return None

        try:
            return self._drone.get_video_frame()
        except Exception as exc:
            print(f"[CameraViewer] Error getting frame: {exc}")
            return None

    def stop(self) -> None:
        """Stop the drone camera stream."""
        if not self._running:
            return

        self._running = False

        try:
            self._drone.stop_video_stream()
        except Exception as exc:
            print(f"[CameraViewer] Error stopping stream: {exc}")

        print("[CameraViewer] stop")

    def is_running(self) -> bool:
        """Return whether camera stream is active."""
        return self._running