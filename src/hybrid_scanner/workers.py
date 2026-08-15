from __future__ import annotations

import threading
from typing import Callable

from loguru import logger

from hybrid_scanner.health import HealthMonitor


class ReconnectingWorker:
    def __init__(
        self,
        *,
        name: str,
        connect: Callable[[], None],
        disconnect: Callable[[], None],
        read: Callable,
        publish: Callable,
        health: HealthMonitor,
        initial_backoff_s: float,
        max_backoff_s: float,
    ) -> None:
        self.name = name
        self.connect = connect
        self.disconnect = disconnect
        self.read = read
        self.publish = publish
        self.health = health
        self.initial_backoff_s = initial_backoff_s
        self.max_backoff_s = max_backoff_s
        self.stop_event = threading.Event()
        self.thread = threading.Thread(target=self._run, daemon=True, name=f"{name}-worker")

    def start(self) -> None:
        self.thread.start()

    def stop(self) -> None:
        self.stop_event.set()
        self.thread.join(timeout=3)
        try:
            self.disconnect()
        except Exception:
            logger.exception("{} disconnect failed", self.name)

    def _run(self) -> None:
        backoff = self.initial_backoff_s
        connected_once = False
        while not self.stop_event.is_set():
            try:
                self.connect()
                if connected_once:
                    self.health.reconnect(self.name)
                connected_once = True
                backoff = self.initial_backoff_s
                while not self.stop_event.is_set():
                    frame = self.read()
                    if frame is None:
                        continue
                    self.publish(frame)
                    self.health.frame(self.name, frame.timestamp_ns)
            except Exception as exc:
                self.health.error(self.name, exc)
                logger.exception("{} worker failure; reconnecting", self.name)
            finally:
                try:
                    self.disconnect()
                except Exception:
                    logger.exception("{} cleanup failed", self.name)
            if not self.stop_event.wait(backoff):
                backoff = min(backoff * 2.0, self.max_backoff_s)
