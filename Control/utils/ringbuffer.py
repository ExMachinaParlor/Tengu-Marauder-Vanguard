"""Thread-safe fixed-size ring buffer for log lines."""

import threading
from collections import deque


class RingBuffer:
    def __init__(self, maxlen: int = 200):
        self._buf: deque[str] = deque(maxlen=maxlen)
        self._lock = threading.Lock()

    def append(self, line: str) -> None:
        with self._lock:
            self._buf.append(line)

    def lines(self) -> list[str]:
        with self._lock:
            return list(self._buf)

    def clear(self) -> None:
        with self._lock:
            self._buf.clear()
