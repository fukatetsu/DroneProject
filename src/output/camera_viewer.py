from __future__ import annotations

import asyncio
from pathlib import Path
from typing import Optional

try:
    import cv2
except ImportError:  # pragma: no cover
    cv2 = None

from ..controllers.drone.drone_controller import DroneController


class CameraViewer:
    """Display the drone camera stream in an OpenCV window."""

    def __init__(self, drone: DroneController) -> None:
        if cv2 is None:
            raise ImportError("opencv-python is required for CameraViewer")

        self._drone = drone
        self._window_title = "Drone Camera"
        self._running = False
        self._update_task: Optional[asyncio.Task[None]] = None
        self._last_frame = None
        self._window_created = False

    def start(self) -> None:
        """Start the video stream and create a window."""
        if self._running:
            return

        self._drone.start_video_stream()
        self._ensure_window()
        self._running = True

        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            self._update_task = None
        else:
            self._update_task = loop.create_task(self._update_loop())

        print("[CameraViewer] start")

    def update(self) -> None:
        """Fetch the latest frame and display it."""
        if not self._running:
            return

        self._ensure_window()

        try:
            frame = self._drone.get_video_frame()
        except Exception as exc:
            print(f"[CameraViewer] Error updating frame: {exc}")
            frame = None

        if frame is None:
            frame = self._create_black_frame()

        self._last_frame = frame
        cv2.imshow(self._window_title, frame)

        key = cv2.waitKey(1) & 0xFF
        if key == ord("q"):
            self.stop()

    async def _update_loop(self) -> None:
        """Continuously refresh the window while the viewer is running."""
        try:
            while self._running:
                self.update()
                await asyncio.sleep(0.016)
        except asyncio.CancelledError:
            pass
        finally:
            self._update_task = None

    def stop(self) -> None:
        """Stop the video stream and close the window."""
        if not self._running:
            return

        self._running = False

        if self._update_task is not None:
            self._update_task.cancel()
            self._update_task = None

        try:
            cv2.destroyWindow(self._window_title)
        except Exception:
            pass

        self._window_created = False
        self._drone.stop_video_stream()
        print("[CameraViewer] stop")

    def _ensure_window(self) -> None:
        if self._window_created or cv2 is None:
            return
        cv2.namedWindow(self._window_title)
        self._window_created = True

    def _create_black_frame(self):
        import numpy as np

        return np.zeros((480, 640, 3), dtype=np.uint8)
