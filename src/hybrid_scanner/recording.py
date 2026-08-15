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
        self._thread = threading.Thread(target=self._writer, daemon=True, name="jsonl-recorder")
        self._thread.start()

    def submit(self, event: dict) -> None:
        try:
            self.queue.put_nowait(event)
        except queue.Full:
            self.dropped += 1

    def _writer(self) -> None:
        with self.path.open("a", encoding="utf-8", buffering=1) as fh:
            while True:
                event = self.queue.get()
                if event is None:
                    break
                fh.write(json.dumps(event, separators=(",", ":"), allow_nan=False) + "\n")

    def close(self) -> None:
        try:
            self.queue.put(None, timeout=1)
        except queue.Full:
            pass
        self._thread.join(timeout=3)
