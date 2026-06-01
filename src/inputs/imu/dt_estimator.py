from __future__ import annotations

import time
from collections import deque
from statistics import median


class DtEstimator:
    def __init__(self, window_size: int = 20) -> None:
        self._previous_time: float | None = None
        self._samples: deque[float] = deque(maxlen=window_size)

    def update(self) -> None:
        now = time.perf_counter()

        if self._previous_time is not None:
            self._samples.append(now - self._previous_time)

        self._previous_time = now

    @property
    def dt(self) -> float:
        if not self._samples:
            return 0.0

        return median(self._samples)

    @property
    def sample_rate(self) -> float:
        dt = self.dt

        if dt <= 0:
            return 0.0

        return 1.0 / dt

    @property
    def ready(self) -> bool:
        return len(self._samples) > 0