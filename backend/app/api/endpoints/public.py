from __future__ import annotations

from fastapi import APIRouter, Depends, Request, Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_db
from app.canaries.monitor import trip_canary
from app.services.event_processor import process_event

router = APIRouter(tags=["Public Canary Callback"])
_PIXEL = b"GIF89a\x01\x00\x01\x00\x80\x00\x00\x00\x00\x00\xff\xff\xff!\xf9\x04\x01\x00\x00\x00\x00,\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02\x02D\x01\x00;"


@router.get("/c/{token}", include_in_schema=False)
async def receive_canary(token: str, request: Request, db: AsyncSession = Depends(get_db)):
    """Public, one-time URL beacon that returns an innocuous tracking pixel."""
    canary = await trip_canary(
        token_value=token,
        db=db,
        source_ip=request.client.host if request.client else "unknown",
        user_agent=request.headers.get("user-agent", "")[:512],
        extra={"path": request.url.path},
    )
    if canary:
        from sqlalchemy import select
        from app.models.event import AttackEvent

        event = await db.scalar(select(AttackEvent).where(AttackEvent.canary_id == canary.id).order_by(AttackEvent.timestamp.desc()).limit(1))
        if event:
            await process_event(db, event)
    return Response(content=_PIXEL, media_type="image/gif", headers={"Cache-Control": "no-store"})
