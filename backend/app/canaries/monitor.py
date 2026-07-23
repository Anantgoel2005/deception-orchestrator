from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.redis_client import redis, STREAMS
from app.models.canary import CanaryStatus, CanaryToken


async def trip_canary(
    token_value: str,
    db: AsyncSession,
    *,
    source_ip: str | None = None,
    user_agent: str | None = None,
    extra: dict | None = None,
) -> Optional[CanaryToken]:
    result = await db.execute(
        select(CanaryToken).where(
            CanaryToken.token_value == token_value,
            CanaryToken.status == CanaryStatus.ACTIVE,
        )
    )
    canary = result.scalar_one_or_none()
    if not canary:
        return None

    canary.status = CanaryStatus.TRIPPED
    canary.tripped_at = datetime.now(timezone.utc)
    canary.trip_source_ip = source_ip
    canary.trip_user_agent = user_agent
    canary.trip_extra = extra
    await db.flush()

    alert_data = {
        "canary_id": str(canary.id),
        "canary_type": canary.canary_type.value,
        "token_value": token_value,
        "planted_location": canary.planted_location or "unknown",
        "source_ip": source_ip or "unknown",
        "user_agent": user_agent or "",
        "tripped_at": canary.tripped_at.isoformat(),
        "extra": extra or {},
    }

    try:
        await redis.xadd(STREAMS["canary_trips"], alert_data, maxlen=10000)
        await redis.xadd(
            STREAMS["alerts"],
            {
                "title": f"Canary tripped: {canary.canary_type.value}", "severity": "high",
                "source": f"canary:{canary.id}", "description": f"Token {token_value} triggered from {source_ip}",
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }, maxlen=10000,
        )
    except Exception:
        # PostgreSQL remains the source of truth if optional stream delivery is down.
        pass

    from app.models.event import AttackEvent, EventType
    event = AttackEvent(
        canary_id=canary.id,
        event_type=EventType.CANARY_TRIP,
        source_ip=source_ip or "unknown",
        parsed_data={
            "canary_type": canary.canary_type.value,
            "token_value": token_value,
            "user_agent": user_agent,
            **(extra or {}),
        },
        threat_score=90,
    )
    db.add(event)
    await db.flush()

    return canary
