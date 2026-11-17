from __future__ import annotations

from dataclasses import dataclass
from typing import Tuple


@dataclass(frozen=True)
class FaceDetection:
    track_id: int
    x: int
    y: int
    width: int
    height: int
    confidence: float = 1.0

    @property
    def center(self) -> Tuple[float, float]:
        return self.x + self.width / 2, self.y + self.height / 2

    @property
    def area(self) -> int:
        return self.width * self.height


@dataclass(frozen=True)
class FaceTrackingState:
    detections: Tuple[FaceDetection, ...]
    frame_width: int
    frame_height: int
    captured_at: float
