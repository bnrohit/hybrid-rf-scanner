from __future__ import annotations

from collections import deque
import threading

from hybrid_scanner.models import RadarFrame, VisionFrame


class FrameBus:
    """Bounded, latest-first sensor bus with timestamp matching.

    The scanner is a real-time product: when consumers fall behind, stale frames
    are intentionally dropped instead of allowing unbounded latency growth.
    """

    def __init__(self, buffer_size: int = 120) -> None:
        self._radar: deque[RadarFrame] = deque(maxlen=buffer_size)
        self._vision: deque[VisionFrame] = deque(maxlen=buffer_size)
        self._lock = threading.Lock()
        self.radar_overwrites = 0
        self.vision_overwrites = 0

    def add_radar(self, frame: RadarFrame) -> None:
        with self._lock:
            if len(self._radar) == self._radar.maxlen:
                self.radar_overwrites += 1
            self._radar.append(frame)

    def add_vision(self, frame: VisionFrame) -> None:
        with self._lock:
            if len(self._vision) == self._vision.maxlen:
                self.vision_overwrites += 1
            self._vision.append(frame)

    def latest_radar_after(self, frame_number: int) -> RadarFrame | None:
        with self._lock:
            if not self._radar:
                return None
            latest = self._radar[-1]
            return None if latest.frame_number == frame_number else latest

    def nearest_vision(self, timestamp_ns: int, max_skew_ms: float) -> tuple[VisionFrame | None, float | None]:
        with self._lock:
            if not self._vision:
                return None, None
            frame = min(self._vision, key=lambda f: abs(f.timestamp_ns - timestamp_ns))
        skew_ms = abs(frame.timestamp_ns - timestamp_ns) / 1_000_000.0
        if skew_ms > max_skew_ms:
            return None, skew_ms
        return frame, skew_ms

    def newest_timestamps(self) -> tuple[int | None, int | None]:
        with self._lock:
            r = self._radar[-1].timestamp_ns if self._radar else None
            v = self._vision[-1].timestamp_ns if self._vision else None
        return r, v
