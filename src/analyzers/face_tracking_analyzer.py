from __future__ import annotations

import math
import shutil
import tempfile
import time
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Sequence, Tuple

try:
    import cv2
except ImportError:  # pragma: no cover - OpenCV is a project dependency
    cv2 = None

from ..models.face_state import FaceDetection, FaceTrackingState


FaceBox = Tuple[int, int, int, int, float]
FaceDetector = Callable[[Any], Sequence[FaceBox]]


class VideoFrameUnavailable(RuntimeError):
    """Raised when a camera frame is absent or too old to use safely."""


class FaceTrackingAnalyzer:
    def __init__(
        self,
        detector: Optional[FaceDetector] = None,
        max_frame_age: float = 0.5,
        max_missed_frames: int = 5,
        match_distance_ratio: float = 1.5,
    ) -> None:
        if max_frame_age <= 0 or max_missed_frames < 0 or match_distance_ratio <= 0:
            raise ValueError("Frame and tracking limits must be positive")
        self._detector = detector
        self.max_frame_age = max_frame_age
        self.max_missed_frames = max_missed_frames
        self.match_distance_ratio = match_distance_ratio
        self._next_track_id = 1
        self._tracks: Dict[int, Tuple[FaceDetection, int]] = {}
        self._face_cascade = None
        if detector is None:
            if cv2 is None:
                raise RuntimeError("OpenCV is required for face detection")
            cascade_path = Path(cv2.data.haarcascades) / "haarcascade_frontalface_default.xml"
            self._face_cascade = self._load_cascade(cascade_path)
            if self._face_cascade.empty():
                raise RuntimeError(f"Unable to load OpenCV face cascade: {cascade_path}")
            self._detector = self._detect_faces

    def analyze(
        self,
        frame: Any,
        captured_at: Optional[float] = None,
        now: Optional[float] = None,
    ) -> FaceTrackingState:
        if frame is None:
            raise VideoFrameUnavailable("No video frame is available")

        current_time = time.monotonic() if now is None else now
        frame_time = current_time if captured_at is None else captured_at
        if current_time - frame_time > self.max_frame_age:
            raise VideoFrameUnavailable("Video frame is stale")
        if frame_time > current_time:
            raise VideoFrameUnavailable("Video frame timestamp is in the future")

        try:
            frame_height, frame_width = frame.shape[:2]
        except (AttributeError, IndexError, TypeError) as error:
            raise ValueError("Video frame must have height and width dimensions") from error
        if frame_width <= 0 or frame_height <= 0:
            raise ValueError("Video frame dimensions must be positive")

        boxes = [
            self._normalize_box(box)
            for box in self._detector(frame)
        ]
        detections = self._assign_tracks(boxes)
        return FaceTrackingState(
            detections=tuple(detections),
            frame_width=int(frame_width),
            frame_height=int(frame_height),
            captured_at=frame_time,
        )

    def _normalize_box(self, box: Sequence[float]) -> FaceBox:
        if len(box) not in (4, 5):
            raise ValueError("Face detector boxes must contain x, y, width, height[, confidence]")
        x, y, width, height = (int(value) for value in box[:4])
        confidence = float(box[4]) if len(box) == 5 else 1.0
        if width <= 0 or height <= 0:
            raise ValueError("Face detector returned a non-positive rectangle")
        return x, y, width, height, confidence

    def _assign_tracks(self, boxes: Sequence[FaceBox]) -> List[FaceDetection]:
        pairs = []
        for index, box in enumerate(boxes):
            x, y, width, height, _ = box
            center_x = x + width / 2
            center_y = y + height / 2
            for track_id, (previous, missed) in self._tracks.items():
                if missed > self.max_missed_frames:
                    continue
                previous_x, previous_y = previous.center
                distance = math.hypot(center_x - previous_x, center_y - previous_y)
                max_distance = max(width, height, previous.width, previous.height) * self.match_distance_ratio
                if distance <= max_distance:
                    pairs.append((distance / max_distance, track_id, index))

        assigned_tracks = set()
        assigned_boxes = set()
        box_tracks: Dict[int, int] = {}
        for _, track_id, index in sorted(pairs):
            if track_id not in assigned_tracks and index not in assigned_boxes:
                assigned_tracks.add(track_id)
                assigned_boxes.add(index)
                box_tracks[index] = track_id

        detections = []
        updated_tracks: Dict[int, Tuple[FaceDetection, int]] = {}
        for index, (x, y, width, height, confidence) in enumerate(boxes):
            track_id = box_tracks.get(index)
            if track_id is None:
                track_id = self._next_track_id
                self._next_track_id += 1
            detection = FaceDetection(track_id, x, y, width, height, confidence)
            detections.append(detection)
            updated_tracks[track_id] = (detection, 0)

        for track_id, (previous, missed) in self._tracks.items():
            if track_id not in assigned_tracks and track_id not in updated_tracks:
                next_missed = missed + 1
                if next_missed <= self.max_missed_frames:
                    updated_tracks[track_id] = (previous, next_missed)

        self._tracks = updated_tracks
        return detections

    def _detect_faces(self, frame: Any) -> Sequence[FaceBox]:
        if cv2 is None or self._face_cascade is None:
            raise RuntimeError("OpenCV face detector is not initialized")
        gray = cv2.cvtColor(frame, cv2.COLOR_RGB2GRAY)
        rectangles = self._face_cascade.detectMultiScale(
            gray,
            scaleFactor=1.1,
            minNeighbors=5,
            minSize=(30, 30),
        )
        return [(int(x), int(y), int(width), int(height), 1.0) for x, y, width, height in rectangles]

    def _load_cascade(self, cascade_path: Path):
        if cv2 is None:
            raise RuntimeError("OpenCV is required for face detection")
        if not cascade_path.is_file():
            raise FileNotFoundError(f"OpenCV face cascade not found: {cascade_path}")
        if str(cascade_path).isascii():
            return cv2.CascadeClassifier(str(cascade_path))

        with tempfile.TemporaryDirectory(prefix="face-cascade-") as temp_dir:
            ascii_path = Path(temp_dir) / cascade_path.name
            if not str(ascii_path).isascii():
                raise RuntimeError("OpenCV cascade path contains unsupported non-ASCII characters")
            shutil.copyfile(str(cascade_path), str(ascii_path))
            return cv2.CascadeClassifier(str(ascii_path))
