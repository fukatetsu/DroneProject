from __future__ import annotations

import asyncio
import hashlib
import tempfile
from pathlib import Path
from typing import Any, Callable, Optional

try:
    import cv2
except ImportError:  # pragma: no cover
    cv2 = None

try:
    import numpy as np
except ImportError:  # pragma: no cover
    np = None

try:
    from PIL import Image
except ImportError:  # pragma: no cover
    Image = None

from ..controllers.drone.drone_controller import DroneController
from .camera_viewer import CameraViewer


class MediaController:
    """Coordinate camera, image, video, and audio media for shows."""

    def __init__(self, drone: DroneController, enabled: bool = True) -> None:
        self._drone = drone
        self._enabled = enabled
        self._camera_enabled = False
        self._camera_viewer: Optional[CameraViewer] = None
        self._display_mode = "Black"
        self._window_title = "Media Controller"
        self._window_created = False
        self._video_task: Optional[asyncio.Task[None]] = None
        self._video_playing = False
        self._master_volume = 100
        self._bgm_volume = 100
        self._se_volume = 100
        self._root_dir = self._resolve_project_root()

    async def enable_camera(self) -> None:
        if not self._enabled:
            self._camera_enabled = False
            return

        if self._camera_enabled:
            return

        self._camera_enabled = True
        if self._camera_viewer is None:
            self._camera_viewer = CameraViewer(self._drone)
        self._camera_viewer.start()
        self.show_camera()

    async def disable_camera(self) -> None:
        if not self._enabled:
            self._camera_enabled = False
            return

        if not self._camera_enabled:
            self.show_black()
            return

        self._camera_enabled = False
        if self._camera_viewer is not None:
            self._camera_viewer.stop()
            self._camera_viewer = None
        self.show_black()

    def is_camera_enabled(self) -> bool:
        return self._camera_enabled

    def set_enabled(self, enabled: bool) -> None:
        self._enabled = enabled
        if not enabled:
            self._camera_enabled = False
            self._stop_video()

    def show_camera(self) -> None:
        if not self._enabled:
            return
        if not self._camera_enabled:
            print("[MediaController] Camera is disabled; showing black screen")
            self.show_black()
            return

        self._display_mode = "Camera"
        self._ensure_window()
        if self._camera_viewer is not None:
            self._camera_viewer.update()

    def show_image(self, path: str) -> None:
        if not self._enabled:
            return
        self._display_mode = "Image"
        self._ensure_window()
        resolved_path = self._resolve_asset_path(path, "images")
        if not resolved_path.exists():
            self.show_black()
            return

        if cv2 is None:
            self.show_black()
            return

        frame = self._load_image_frame(resolved_path)
        if frame is None:
            self.show_black()
            return
        self._display_frame(frame)

    def show_black(self) -> None:
        if not self._enabled:
            return
        self._display_mode = "Black"
        self._ensure_window()
        black_frame = self._create_black_frame()
        self._display_frame(black_frame)

    def play_video(self, path: str, on_finished: Optional[Callable[[], None]] = None) -> None:
        if not self._enabled:
            self._invoke_callback(on_finished)
            return

        self._display_mode = "Video"
        self._stop_video()

        async def _run_video() -> None:
            if cv2 is None:
                self._video_playing = False
                self._invoke_callback(on_finished)
                return

            self._video_playing = True
            self._ensure_window()
            resolved_path = self._resolve_asset_path(path, "videos")
            if not resolved_path.exists():
                self._video_playing = False
                self._invoke_callback(on_finished)
                return

            capture = self._open_video_capture(resolved_path)
            if capture is None:
                self._video_playing = False
                self._invoke_callback(on_finished)
                return
            try:
                while self._video_playing:
                    ok, frame = capture.read()
                    if not ok:
                        break
                    self._display_frame(frame)
                    await asyncio.sleep(0.03)
            finally:
                capture.release()
                self._video_playing = False
                self._invoke_callback(on_finished)

        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            return

        self._video_task = loop.create_task(_run_video())

    def stop_video(self) -> None:
        self._stop_video()

    def is_playing_video(self) -> bool:
        return self._video_playing

    def play_bgm(self, path: str, loop: bool = False, on_finished: Optional[Callable[[], None]] = None) -> None:
        del loop
        self._invoke_callback(on_finished)

    def stop_bgm(self) -> None:
        return None

    def play_se(self, path: str, on_finished: Optional[Callable[[], None]] = None) -> None:
        self._invoke_callback(on_finished)

    def stop_all_audio(self) -> None:
        self.stop_bgm()
        self.stop_video()

    def set_master_volume(self, volume: int) -> None:
        self._master_volume = self._clamp_volume(volume)

    def set_bgm_volume(self, volume: int) -> None:
        self._bgm_volume = self._clamp_volume(volume)

    def set_se_volume(self, volume: int) -> None:
        self._se_volume = self._clamp_volume(volume)

    def set_window(self, monitor: int, x: int, y: int, width: int, height: int) -> None:
        if not self._enabled:
            return
        del monitor
        self._ensure_window()
        if cv2 is not None and hasattr(cv2, "resizeWindow"):
            try:
                cv2.resizeWindow(self._window_title, width, height)
            except Exception:
                pass
        if cv2 is not None and hasattr(cv2, "moveWindow"):
            try:
                cv2.moveWindow(self._window_title, x, y)
            except Exception:
                pass

    def set_fullscreen(self, enabled: bool) -> None:
        if not self._enabled or cv2 is None:
            return
        self._ensure_window()
        if hasattr(cv2, "setWindowProperty"):
            try:
                prop = cv2.WND_PROP_FULLSCREEN if hasattr(cv2, "WND_PROP_FULLSCREEN") else None
                if prop is not None:
                    cv2.setWindowProperty(self._window_title, prop, 1 if enabled else 0)
            except Exception:
                pass

    def _stop_video(self) -> None:
        self._video_playing = False
        if self._video_task is not None:
            self._video_task.cancel()
            self._video_task = None

    def _ensure_window(self) -> None:
        if self._window_created or cv2 is None:
            return
        cv2.namedWindow(self._window_title)
        self._window_created = True

    def _display_frame(self, frame: Any) -> None:
        if cv2 is None:
            return
        self._ensure_window()
        try:
            cv2.imshow(self._window_title, frame)
        except Exception as exc:
            print(f"[MediaController] Failed to display frame: {exc}")

        try:
            cv2.waitKey(1)
        except Exception:
            pass

    def _create_black_frame(self):
        if np is None:
            return None
        return np.zeros((480, 640, 3), dtype=np.uint8)

    def _load_image_frame(self, resolved_path: Path) -> Any:
        if cv2 is None:
            return None

        try:
            if Image is not None:
                with Image.open(resolved_path) as image:
                    rgb_image = image.convert("RGB")
                    if np is not None:
                        return np.array(rgb_image)[:, :, ::-1]
        except Exception:
            pass

        return None

    def _open_video_capture(self, resolved_path: Path) -> Any:
        if cv2 is None:
            return None

        for candidate in (resolved_path, self._copy_asset_to_ascii_path(resolved_path)):
            try:
                if not candidate.exists():
                    continue
                capture = cv2.VideoCapture(str(candidate))
                if capture is not None and capture.isOpened():
                    return capture
                if capture is not None:
                    capture.release()
            except Exception:
                pass

        return None

    def _copy_asset_to_ascii_path(self, resolved_path: Path) -> Path:
        if not resolved_path.exists():
            return resolved_path

        temp_dir = Path(tempfile.gettempdir())
        digest = hashlib.sha1(str(resolved_path).encode("utf-8")).hexdigest()[:12]
        temp_path = temp_dir / f"media_{digest}{resolved_path.suffix}"
        try:
            if not temp_path.exists() or temp_path.stat().st_mtime < resolved_path.stat().st_mtime:
                temp_path.write_bytes(resolved_path.read_bytes())
        except Exception:
            return resolved_path
        return temp_path

    def _resolve_asset_path(self, path: str, asset_type: str) -> Path:
        return self._root_dir / "assets" / asset_type / path

    def _resolve_project_root(self) -> Path:
        return Path(__file__).resolve().parents[2]

    def _invoke_callback(self, callback: Optional[Callable[[], None]]) -> None:
        if callback is None:
            return

        if inspect.iscoroutinefunction(callback):
            try:
                loop = asyncio.get_running_loop()
            except RuntimeError:
                asyncio.run(callback())
            else:
                loop.create_task(callback())
            return

        callback()

    def _clamp_volume(self, volume: int) -> int:
        return max(0, min(100, int(volume)))
