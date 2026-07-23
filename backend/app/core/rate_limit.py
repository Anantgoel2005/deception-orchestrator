from __future__ import annotations

import time
from collections import defaultdict, deque


class FixedWindowRateLimiter:
    """Small dependency-free limiter for the two public entry points.

    Production deployments should additionally enforce limits at Caddy or an
    edge proxy; this prevents accidental brute force in a single API process.
    """

    def __init__(self) -> None:
        self._hits: dict[str, deque[float]] = defaultdict(deque)

    def allowed(self, key: str, limit: int, seconds: int) -> bool:
        now = time.monotonic()
        hits = self._hits[key]
        while hits and hits[0] <= now - seconds:
            hits.popleft()
        if len(hits) >= limit:
            return False
        hits.append(now)
        return True


rate_limiter = FixedWindowRateLimiter()
