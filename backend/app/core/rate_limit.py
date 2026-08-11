from __future__ import annotations

import time
from threading import Lock
from collections import defaultdict, deque


class FixedWindowRateLimiter:
    """Small dependency-free limiter for the two public entry points.

    Production deployments should additionally enforce limits at Caddy or an
    edge proxy; this prevents accidental brute force in a single API process.
    """

    def __init__(self, max_keys: int = 10_000) -> None:
        self._hits: dict[str, deque[float]] = defaultdict(deque)
        self._lock = Lock()
        self._max_keys = max_keys

    def allowed(self, key: str, limit: int, seconds: int) -> bool:
        now = time.monotonic()
        with self._lock:
            if key not in self._hits and len(self._hits) >= self._max_keys:
                self._prune(now)
                if len(self._hits) >= self._max_keys:
                    return False
            hits = self._hits[key]
            while hits and hits[0] <= now - seconds:
                hits.popleft()
            if len(hits) >= limit:
                return False
            hits.append(now)
            return True

    def _prune(self, now: float) -> None:
        stale = [key for key, hits in self._hits.items() if not hits or hits[-1] <= now - 3600]
        for key in stale:
            self._hits.pop(key, None)

    def reset(self) -> None:
        with self._lock:
            self._hits.clear()


rate_limiter = FixedWindowRateLimiter()
