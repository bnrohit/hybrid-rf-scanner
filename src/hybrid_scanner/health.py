from __future__ import annotations

from dataclasses import dataclass
import math
import threading
import time


@dataclass
class _SensorHealth:
    frames: int = 0
    errors: int = 0
    reconnects: int = 0
    last_frame_ns: int | None = None
    last_error: str | None = None


class HealthMonitor:
    def __init__(self, stale_sensor_ms: float) -> None:
        self.stale_sensor_ms = stale_sensor_ms
        self._sensors = {"radar": _SensorHealth(), "vision": _SensorHealth()}
        self._lock = threading.Lock()

    def frame(self, sensor: str, timestamp_ns: int) -> None:
        with self._lock:
            s = self._sensors[sensor]
            s.frames += 1
            s.last_frame_ns = timestamp_ns
            s.last_error = None

    def error(self, sensor: str, error: Exception | str) -> None:
        with self._lock:
            s = self._sensors[sensor]
            s.errors += 1
            s.last_error = str(error)

    def reconnect(self, sensor: str) -> None:
        with self._lock:
            self._sensors[sensor].reconnects += 1

    def trust(self, sensor: str, now_ns: int | None = None) -> float:
        now_ns = now_ns or time.monotonic_ns()
        with self._lock:
            s = self._sensors[sensor]
            frames, errors, last = s.frames, s.errors, s.last_frame_ns
        success = frames / max(frames + errors, 1)
        if last is None:
            freshness = 0.0
        else:
            age_ms = max(0.0, (now_ns - last) / 1e6)
            freshness = math.exp(-age_ms / max(self.stale_sensor_ms, 1.0))
        return max(0.0, min(1.0, success * freshness))

    def snapshot(self, now_ns: int | None = None) -> dict:
        now_ns = now_ns or time.monotonic_ns()
        with self._lock:
            copied = {name: _SensorHealth(**vars(s)) for name, s in self._sensors.items()}
        out = {}
        for name, s in copied.items():
            age_ms = None if s.last_frame_ns is None else max(0.0, (now_ns - s.last_frame_ns) / 1e6)
            out[name] = {
                "frames": s.frames,
                "errors": s.errors,
                "reconnects": s.reconnects,
                "last_error": s.last_error,
                "age_ms": age_ms,
                "trust": self.trust(name, now_ns),
                "stale": age_ms is None or age_ms > self.stale_sensor_ms,
            }
        return out
