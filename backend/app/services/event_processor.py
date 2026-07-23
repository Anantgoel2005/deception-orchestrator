from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.honeypot import Honeypot
from app.models.event import AttackEvent
from app.services.alert_engine import evaluate_event
from app.services.event_ingestor import enrich_event


async def process_event(db: AsyncSession, event: AttackEvent) -> None:
    """Run the single, deterministic event pipeline used by decoys and demos."""
    await enrich_event(event)
    if event.honeypot_id:
        honeypot = await db.scalar(select(Honeypot).where(Honeypot.id == event.honeypot_id))
        if honeypot:
            honeypot.total_connections += 1 if event.event_type.value == "connection" else 0
            honeypot.total_commands += 1 if event.event_type.value == "command" else 0
    await evaluate_event(db, event)
