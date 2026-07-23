from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.event import AttackEvent
from app.models.honeypot import Honeypot
from app.utils.mitre import MITRE_TECHNIQUE_LOOKUP


async def get_attack_timeline(
    db: AsyncSession,
    hours: int = 24,
    honeypot_id: uuid.UUID | None = None,
) -> list[dict]:
    cutoff = datetime.now(timezone.utc) - timedelta(hours=hours)

    conditions = [AttackEvent.timestamp >= cutoff]
    if honeypot_id:
        conditions.append(AttackEvent.honeypot_id == honeypot_id)

    result = await db.execute(
        select(
            func.date_trunc("hour", AttackEvent.timestamp).label("hour"),
            func.count(AttackEvent.id).label("count"),
        )
        .where(*conditions)
        .group_by("hour")
        .order_by("hour")
    )

    return [
        {"hour": str(row.hour), "count": row.count}
        for row in result.all()
    ]


async def get_top_attackers(
    db: AsyncSession,
    limit: int = 10,
) -> list[dict]:
    result = await db.execute(
        select(
            AttackEvent.source_ip,
            func.count(AttackEvent.id).label("count"),
            func.max(AttackEvent.threat_score).label("max_threat"),
        )
        .group_by(AttackEvent.source_ip)
        .order_by(func.count(AttackEvent.id).desc())
        .limit(limit)
    )

    return [
        {"ip": row.source_ip, "event_count": row.count, "max_threat": row.max_threat}
        for row in result.all()
    ]


async def get_ttp_summary(
    db: AsyncSession,
) -> list[dict]:
    result = await db.execute(
        select(
            AttackEvent.mitre_technique,
            func.count(AttackEvent.id).label("count"),
        )
        .where(AttackEvent.mitre_technique.isnot(None))
        .group_by(AttackEvent.mitre_technique)
        .order_by(func.count(AttackEvent.id).desc())
    )

    from app.utils.mitre import MITRE_TECHNIQUE_LOOKUP

    return [
        {
            "technique_id": row.mitre_technique,
            "name": MITRE_TECHNIQUE_LOOKUP.get(row.mitre_technique, {}).get("name", "Unknown"),
            "tactic": MITRE_TECHNIQUE_LOOKUP.get(row.mitre_technique, {}).get("tactic", "Unknown"),
            "count": row.count,
        }
        for row in result.all()
    ]


async def get_honeypot_metrics(
    db: AsyncSession,
) -> list[dict]:
    result = await db.execute(
        select(
            Honeypot.name,
            Honeypot.honeypot_type,
            Honeypot.status,
            Honeypot.total_connections,
            Honeypot.total_commands,
            Honeypot.unique_attackers,
            Honeypot.ip_address,
        )
    )

    return [
        {
            "name": row.name,
            "type": row.honeypot_type.value if hasattr(row.honeypot_type, "value") else str(row.honeypot_type),
            "status": row.status.value if hasattr(row.status, "value") else str(row.status),
            "connections": row.total_connections,
            "commands": row.total_commands,
            "unique_attackers": row.unique_attackers,
            "ip": row.ip_address,
        }
        for row in result.all()
    ]
