from __future__ import annotations

import threading
from typing import Callable


class PollScheduler:
    def __init__(self, interval_seconds: Callable[[], int], on_tick: Callable[[], None]) -> None:
        self._interval_seconds = interval_seconds
        self._on_tick = on_tick
        self._timer: threading.Timer | None = None
        self._lock = threading.Lock()
        self._running = False

    def start(self) -> None:
        with self._lock:
            if self._running:
                return
            self._running = True
            self._schedule_next()

    def stop(self) -> None:
        with self._lock:
            self._running = False
            if self._timer is not None:
                self._timer.cancel()
                self._timer = None

    def reschedule(self) -> None:
        with self._lock:
            if not self._running:
                return
            if self._timer is not None:
                self._timer.cancel()
            self._schedule_next()

    def _schedule_next(self) -> None:
        delay = max(30, self._interval_seconds())

        def _fire() -> None:
            with self._lock:
                if not self._running:
                    return
            try:
                self._on_tick()
            finally:
                with self._lock:
                    if self._running:
                        self._schedule_next()

        self._timer = threading.Timer(delay, _fire)
        self._timer.daemon = True
        self._timer.start()
