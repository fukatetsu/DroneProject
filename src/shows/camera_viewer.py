from __future__ import annotations

import asyncio
import contextlib
from typing import Optional

try:
    import cv2
except ImportError:
    cv2 = None

from ..controllers.drone.drone_controller import DroneController


class CameraViewer:
    """
    Displays video stream from DroneController in an OpenCV window.
    
    Responsibilities:
    - Display video frames from DroneController
    - Manage display window lifecycle (create/destroy)
    - Update frames continuously in background task
    """

    def __init__(self, drone: DroneController) -> None:
        """
        Initialize CameraViewer.
        
        Args:
            drone: DroneController instance providing video frames
        """
        if cv2 is None:
            raise ImportError("opencv-python is required for CameraViewer")
        
        self._drone = drone
        self._window_title = "Drone Camera"
        self._running = False
        self._update_task: Optional[asyncio.Task[None]] = None

    def start(self) -> None:
        """
        Start video display.
        
        Creates OpenCV window, starts video stream from drone,
        and begins background update task.
        """
        if self._running:
            return
        
        self._drone.start_video_stream()
        cv2.namedWindow(self._window_title)
        self._running = True
        
        # Start background update task
        if self._update_task is None:
            self._update_task = asyncio.create_task(self._update_loop())
        
        print("[CameraViewer] start")

    async def _update_loop(self) -> None:
        """
        Background task that continuously updates the display.
        
        Runs independently from command execution,
        ensuring video updates at ~60 FPS.
        """
        try:
            while self._running:
                try:
                    frame = self._drone.get_video_frame()
                    
                    if frame is None:
                        black_frame = self._create_black_frame()
                        cv2.imshow(self._window_title, black_frame)
                    else:
                        cv2.imshow(self._window_title, frame)
                    
                    # Handle window events (keep window responsive)
                    key = cv2.waitKey(1) & 0xFF
                    if key == ord('q'):
                        self._running = False
                        
                except Exception as e:
                    print(f"[CameraViewer] Error updating frame: {e}")
                    # Continue running despite errors
                
                # Small sleep to yield control to event loop
                await asyncio.sleep(0.016)  # ~60 FPS
        except asyncio.CancelledError:
            pass

    def stop(self) -> None:
        """
        Stop video display.
        
        Stops background update task, closes OpenCV window,
        and stops video stream from drone.
        """
        if not self._running:
            return
        
        self._running = False
        
        # Cancel the update task
        if self._update_task is not None:
            self._update_task.cancel()
            self._update_task = None
        
        cv2.destroyWindow(self._window_title)
        self._drone.stop_video_stream()
        print("[CameraViewer] stop")

    def _create_black_frame(self):
        """
        Create a black frame for display when camera is not connected.
        
        Returns:
            numpy.ndarray: Black frame (480x640 BGR)
        """
        import numpy as np
        return np.zeros((480, 640, 3), dtype=np.uint8)
