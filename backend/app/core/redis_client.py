from __future__ import annotations

import redis.asyncio as aioredis

from app.config import settings

redis = aioredis.from_url(settings.redis_url, decode_responses=True)


STREAMS = {
    "events": "deception:events",
    "alerts": "deception:alerts",
    "canary_trips": "deception:canary_trips",
    "engagements": "deception:engagements",
}
