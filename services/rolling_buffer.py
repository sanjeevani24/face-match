import time
from collections import deque
from dataclasses import dataclass
from typing import Optional


@dataclass
class PoseEarSample:
    timestamp: float
    direction: Optional[str]
    yaw: Optional[float]
    pitch: Optional[float]
    ear: Optional[float]
    blink: bool


class RollingBuffer:
    def __init__(self, window_seconds: float = 10.0):
        self.window_seconds = window_seconds
        self._samples: deque[PoseEarSample] = deque()

    def push(self, sample: PoseEarSample) -> None:
        self._samples.append(sample)
        self._prune(sample.timestamp)

    def _prune(self, now: float) -> None:
        cutoff = now - self.window_seconds
        while self._samples and self._samples[0].timestamp < cutoff:
            self._samples.popleft()

    def snapshot(self) -> list[PoseEarSample]:
        return list(self._samples)

    def window(self, start_ts: float, end_ts: float) -> list[PoseEarSample]:
        return [s for s in self._samples if start_ts <= s.timestamp <= end_ts]

    def direction_seen_in_window(self, direction: str, start_ts: float, end_ts: float) -> bool:
        return any(s.direction == direction for s in self.window(start_ts, end_ts))

    def blink_seen_in_window(self, start_ts: float, end_ts: float) -> bool:
        return any(s.blink for s in self.window(start_ts, end_ts))