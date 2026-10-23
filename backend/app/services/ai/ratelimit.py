"""In-process sliding-window rate limiter for the paid AI endpoints."""
from __future__ import annotations

import threading
import time
from collections import defaultdict, deque
from typing import Deque, Dict, Tuple


class SlidingWindowLimiter:
    def __init__(self, limit: int = 20, window_seconds: float = 60.0):
        self.limit = int(limit)
        self.window = float(window_seconds)
        self._hits: Dict[str, Deque[float]] = defaultdict(deque)
        self._lock = threading.Lock()

    def check(self, key: str) -> Tuple[bool, float]:
        """Return (allowed, retry_after_seconds)."""
        if self.limit <= 0:
            return True, 0.0
        now = time.time()
        with self._lock:
            q = self._hits[key]
            while q and now - q[0] > self.window:
                q.popleft()
            if len(q) >= self.limit:
                retry = self.window - (now - q[0])
                return False, max(0.0, retry)
            q.append(now)
            return True, 0.0

    def reset(self) -> None:
        with self._lock:
            self._hits.clear()
