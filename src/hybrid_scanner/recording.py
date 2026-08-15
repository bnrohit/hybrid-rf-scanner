from __future__ import annotations

import json
from pathlib import Path
import queue
import threading


class JsonlRecorder:
    """Non-blocking bounded recorder; real-time processing wins over disk I/O."""

    def __init__(self, path: str, queue_size: int = 10000) -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.queue: queue.Queue[dict | None] = queue.Queue(maxsize=queue_size)
        self.dropped = 0
        self.written = 0
        self.last_error: str | None = None
        self._lock = threading.Lock()
        self._closed = False
        self._thread = threading.Thread(target=self._writer, daemon=True, name="jsonl-recorder")
        self._thread.start()

    def submit(self, event: dict) -> bool:
        with self._lock:
            if self._closed:
                return False
        try:
            self.queue.put_nowait(event)
            return True
        except queue.Full:
            with self._lock:
                self.dropped += 1
            return False

    def _writer(self) -> None:
        try:
            with self.path.open("a", encoding="utf-8", buffering=1) as fh:
                while True:
                    event = self.queue.get()
                    try:
                        if event is None:
                            return
                        fh.write(json.dumps(event, separators=(",", ":"), allow_nan=False) + "\n")
                        with self._lock:
                            self.written += 1
                    except Exception as exc:
                        with self._lock:
                            self.dropped += 1
                            self.last_error = str(exc)
                    finally:
                        self.queue.task_done()
        except Exception as exc:
            with self._lock:
                self.last_error = str(exc)

    def snapshot(self) -> dict:
        with self._lock:
            return {
                "written": self.written,
                "dropped": self.dropped,
                "last_error": self.last_error,
                "queue_depth": self.queue.qsize(),
                "closed": self._closed,
            }

    def close(self) -> None:
        with self._lock:
            if self._closed:
                return
            self._closed = True
        try:
            self.queue.put(None, timeout=3)
        except queue.Full:
            with self._lock:
                self.last_error = "recorder shutdown timed out while queue was full"
            return
        self._thread.join(timeout=5)
        if self._thread.is_alive():
            with self._lock:
                self.last_error = "recorder writer did not stop within timeout"
