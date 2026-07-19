from __future__ import annotations

import asyncio
import inspect
from pathlib import Path
from typing import Any, Callable, Optional

try:
    import cv2
except ImportError:
    cv2 = None

try:
    import numpy as np
except ImportError:
    np = None

try:
    from PIL import Image
except ImportError:
    Image = None


from ..controllers.drone.drone_controller import DroneController
from .camera_viewer import CameraViewer


class MediaController:
    """Manage all media output.

    Show only changes output state.
    This class owns rendering.
    """

    def __init__(
        self,
        drone: DroneController,
        enabled: bool = True,
    ) -> None:

        self._drone = drone
        self._enabled = enabled

        # camera
        self._camera_enabled = False
        self._camera_viewer: Optional[CameraViewer] = None

        # display
        self._display_mode = "Black"

        self._image_frame = None
        self._video_frame = None

        # tasks
        self._render_task: Optional[asyncio.Task] = None
        self._video_task: Optional[asyncio.Task] = None

        self._video_playing = False

        # window
        self._window_title = "Drone Media Output"
        self._window_created = False

        # audio placeholder
        self._master_volume = 100
        self._bgm_volume = 100
        self._se_volume = 100

        self._root_dir = self._resolve_project_root()


    # =====================================================
    # Camera
    # =====================================================

    async def enable_camera(self) -> None:

        if not self._enabled:
            return

        if self._camera_viewer is None:
            self._camera_viewer = CameraViewer(
                self._drone
            )

        if not self._camera_enabled:
            self._camera_viewer.start()
            self._camera_enabled = True


    async def disable_camera(self) -> None:

        self._camera_enabled = False

        if self._camera_viewer is not None:
            self._camera_viewer.stop()
            self._camera_viewer = None

        self.show_black()



    def is_camera_enabled(self) -> bool:
        return self._camera_enabled



    def show_camera(self) -> None:

        if not self._enabled:
            return

        self._ensure_render_loop()

        if not self._camera_enabled:
            self.show_black()
            return

        self._display_mode = "Camera"

    async def shutdown(self) -> None:
        self._stop_video()

        if self._camera_viewer is not None:
            self._camera_viewer.stop()
            self._camera_viewer = None

        if self._render_task is not None:
            self._render_task.cancel()
            try:
                await self._render_task
            except asyncio.CancelledError:
                pass
            self._render_task = None

        if cv2 is not None and self._window_created:
            cv2.destroyWindow(self._window_title)
            cv2.waitKey(1)   # destroyWindowを反映させる
            self._window_created = False



    # =====================================================
    # Image
    # =====================================================

    def show_image(self, path: str) -> None:

        if not self._enabled:
            return

        self._ensure_render_loop()

        resolved_path = self._resolve_asset_path(
            path,
            "images",
        )

        frame = self._load_image_frame(
            resolved_path
        )

        if frame is None:
            self.show_black()
            return

        self._image_frame = frame
        self._display_mode = "Image"



    # =====================================================
    # Video
    # =====================================================

    def play_video(
        self,
        path: str,
        on_finished: Optional[Callable[[], None]] = None,
    ) -> None:

        if not self._enabled:
            return

        self._ensure_render_loop()

        self._stop_video()

        self._video_task = asyncio.create_task(
            self._video_loop(
                path,
                on_finished,
            )
        )



    async def _video_loop(
        self,
        path: str,
        on_finished: Optional[Callable[[], None]],
    ) -> None:

        if cv2 is None:
            return


        resolved_path = self._resolve_asset_path(
            path,
            "videos",
        )

        capture = cv2.VideoCapture(
            str(resolved_path)
        )


        if not capture.isOpened():
            print(
                f"[MediaController] Cannot open video: {resolved_path}"
            )
            return


        self._video_playing = True
        self._display_mode = "Video"


        fps = capture.get(
            cv2.CAP_PROP_FPS
        )

        if fps <= 0:
            fps = 30


        interval = 1 / fps


        try:

            while self._video_playing:

                ok, frame = capture.read()

                if not ok:
                    break


                self._video_frame = frame

                await asyncio.sleep(
                    interval
                )


        except asyncio.CancelledError:
            pass


        finally:

            capture.release()

            self._video_playing = False

            if on_finished:
                self._invoke_callback(
                    on_finished
                )



    def stop_video(self) -> None:

        self._stop_video()



    def is_playing_video(self) -> bool:
        return self._video_playing



    def _stop_video(self):

        self._video_playing = False

        if self._video_task is not None:
            self._video_task.cancel()
            self._video_task = None



    # =====================================================
    # Display
    # =====================================================

    def show_black(self) -> None:

        if not self._enabled:
            return

        self._ensure_render_loop()

        self._display_mode = "Black"



    async def _render_loop(self):

        try:

            while True:

                frame = self._get_current_frame()

                if frame is None:
                    frame = self._create_black_frame()


                self._display_frame(
                    frame
                )


                await asyncio.sleep(
                    0.016
                )


        except asyncio.CancelledError:
            pass



    def _get_current_frame(self):

        if self._display_mode == "Camera":

            if self._camera_viewer is None:
                return None

            return self._camera_viewer.get_frame()



        if self._display_mode == "Video":

            return self._video_frame



        if self._display_mode == "Image":

            return self._image_frame



        return self._create_black_frame()



    def _display_frame(
        self,
        frame: Any,
    ) -> None:

        if cv2 is None:
            return


        self._ensure_window()


        cv2.imshow(
            self._window_title,
            frame,
        )

        cv2.waitKey(
            1
        )



    # =====================================================
    # Window
    # =====================================================

    def set_window(
        self,
        monitor: int,
        x: int,
        y: int,
        width: int,
        height: int,
    ) -> None:

        if not self._enabled:
            return

        del monitor

        self._ensure_window()

        cv2.resizeWindow(
            self._window_title,
            width,
            height,
        )

        cv2.moveWindow(
            self._window_title,
            x,
            y,
        )



    def set_fullscreen(self, enabled: bool) -> None:
        if cv2 is None:
            return

        self._ensure_window()

        cv2.setWindowProperty(
            self._window_title,
            cv2.WND_PROP_FULLSCREEN,
            cv2.WINDOW_FULLSCREEN if enabled else cv2.WINDOW_NORMAL,
        )

        cv2.waitKey(1)



    def _ensure_window(self):

        if self._window_created:
            return

        if cv2 is None:
            return

        cv2.namedWindow(
            self._window_title,
            cv2.WINDOW_NORMAL,
        )

        self._window_created = True



    def _ensure_render_loop(self):

        if self._render_task is not None:
            return

        try:
            loop = asyncio.get_running_loop()

        except RuntimeError:
            return


        self._render_task = loop.create_task(
            self._render_loop()
        )



    # =====================================================
    # Audio (placeholder)
    # =====================================================

    def play_bgm(
        self,
        path: str,
        loop: bool = False,
        on_finished=None,
    ):
        del path, loop

        if on_finished:
            self._invoke_callback(
                on_finished
            )


    def stop_bgm(self):
        pass



    def play_se(
        self,
        path: str,
        on_finished=None,
    ):
        del path

        if on_finished:
            self._invoke_callback(
                on_finished
            )


    def stop_all_audio(self):
        self.stop_bgm()



    def set_master_volume(
        self,
        volume: int,
    ):
        self._master_volume = self._clamp_volume(volume)



    def set_bgm_volume(
        self,
        volume: int,
    ):
        self._bgm_volume = self._clamp_volume(volume)



    def set_se_volume(
        self,
        volume: int,
    ):
        self._se_volume = self._clamp_volume(volume)



    # =====================================================
    # Utility
    # =====================================================

    def set_enabled(
        self,
        enabled: bool,
    ):

        self._enabled = enabled

        if not enabled:
            self._stop_video()



    def _create_black_frame(self):

        if np is None:
            return None

        return np.zeros(
            (480,640,3),
            dtype=np.uint8,
        )



    def _load_image_frame(
        self,
        path: Path,
    ):

        if Image is None or np is None:
            return None


        try:

            with Image.open(path) as img:

                rgb = img.convert(
                    "RGB"
                )

                return np.array(rgb)[:, :, ::-1]


        except Exception:

            return None



    def _resolve_asset_path(
        self,
        path: str,
        asset_type: str,
    ) -> Path:

        return (
            self._root_dir
            / "assets"
            / asset_type
            / path
        )



    def _resolve_project_root(self):

        return Path(__file__).resolve().parents[2]



    def _invoke_callback(
        self,
        callback,
    ):

        if inspect.iscoroutinefunction(callback):

            try:
                loop = asyncio.get_running_loop()
                loop.create_task(
                    callback()
                )

            except RuntimeError:
                asyncio.run(
                    callback()
                )

        else:

            callback()



    def _clamp_volume(
        self,
        volume: int,
    ):

        return max(
            0,
            min(
                100,
                int(volume),
            ),
        )