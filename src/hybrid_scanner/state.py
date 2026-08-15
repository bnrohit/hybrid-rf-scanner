from __future__ import annotations

import copy
import threading
import time
from typing import Any


class StatusStore:
    def __init__(self) -> None:
        self._lock = threading.RLock()
        self._status: dict[str, Any] = {
            "healthy": False,
            "ready": False,
            "started_at_epoch_s": time.time(),
            "started_at_monotonic_ns": time.monotonic_ns(),
            "mode": "unknown",
            "frame_number": 0,
            "sync_skew_ms": None,
            "measurements": [],
            "tracks": [],
            "guidance": None,
            "calibration": {},
            "sensors": {},
            "last_update_monotonic_ns": None,
            "last_error": None,
            "recorder_dropped": 0,
        }

    def update(self, **kwargs: Any) -> None:
        with self._lock:
            self._status.update(kwargs)
            self._status["last_update_monotonic_ns"] = time.monotonic_ns()

    def snapshot(self) -> dict[str, Any]:
        with self._lock:
            return copy.deepcopy(self._status)
