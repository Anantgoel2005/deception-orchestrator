from __future__ import annotations

import uuid
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from pydantic import BaseModel, Field
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_current_user, get_db
from app.config import settings
from app.models.canary import CanaryStatus, CanaryToken, CanaryType

router = APIRouter()


class CanaryCreate(BaseModel):
    canary_type: CanaryType
    token_value: str = Field(..., min_length=1, max_length=2048)
    token_metadata: dict | None = None
    planted_location: str | None = None
    expires_at: datetime | None = None


class CanaryOut(BaseModel):
    id: uuid.UUID
    canary_type: CanaryType
    status: CanaryStatus
    token_value: str
    token_metadata: dict | None = None
    planted_location: str | None
    tripped_at: datetime | None
    trip_source_ip: str | None
    trip_user_agent: str | None
    trip_extra: dict | None
    created_at: datetime
    expires_at: datetime | None
    callback_url: str | None = None

    model_config = {"from_attributes": True}


class CanaryListOut(BaseModel):
    items: list[CanaryOut]
    total: int


class CanaryUpdate(BaseModel):
    status: CanaryStatus | None = None
    planted_location: str | None = None


class CanaryGenerateRequest(BaseModel):
    canary_type: CanaryType
    count: int = Field(default=1, ge=1, le=100)
    planted_location: str | None = None


@router.get("", response_model=CanaryListOut)
async def list_canaries(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    status: CanaryStatus | None = None,
    canary_type: CanaryType | None = None,
    db: AsyncSession = Depends(get_db),
    _user: str = Depends(get_current_user),
):
    conditions = []
    if status:
        conditions.append(CanaryToken.status == status)
    if canary_type:
        conditions.append(CanaryToken.canary_type == canary_type)

    total_q = select(func.count(CanaryToken.id))
    items_q = select(CanaryToken).order_by(CanaryToken.created_at.desc())
    if conditions:
        total_q = total_q.where(*conditions)
        items_q = items_q.where(*conditions)

    total_result = await db.execute(total_q)
    total = total_result.scalar() or 0

    items_result = await db.execute(items_q.offset(skip).limit(limit))
    items = items_result.scalars().all()

    return CanaryListOut(
        items=[_canary_out(c) for c in items],
        total=total,
    )


@router.post("", response_model=CanaryOut, status_code=status.HTTP_201_CREATED)
async def create_canary(
    payload: CanaryCreate,
    db: AsyncSession = Depends(get_db),
    _user: str = Depends(get_current_user),
):
    canary = CanaryToken(
        canary_type=payload.canary_type,
        token_value=payload.token_value,
        token_metadata=payload.token_metadata,
        planted_location=payload.planted_location,
        expires_at=payload.expires_at,
    )
    db.add(canary)
    await db.flush()
    await db.refresh(canary)
    return _canary_out(canary)


@router.post("/generate", response_model=list[CanaryOut], status_code=status.HTTP_201_CREATED)
async def generate_canaries(
    payload: CanaryGenerateRequest,
    db: AsyncSession = Depends(get_db),
    _user: str = Depends(get_current_user),
):
    from app.canaries.generator import generate_tokens

    if payload.canary_type != CanaryType.URL:
        raise HTTPException(status_code=422, detail="Only URL canaries are supported in v1")
    tokens = generate_tokens(payload.canary_type, payload.count)
    canaries = []
    for token_value in tokens:
        canary = CanaryToken(
            canary_type=payload.canary_type,
            token_value=token_value,
            planted_location=payload.planted_location,
        )
        db.add(canary)
        canaries.append(canary)

    await db.flush()
    for c in canaries:
        await db.refresh(c)

    return [_canary_out(c) for c in canaries]


class TripRequest(BaseModel):
    token_value: str


@router.post("/trip")
async def trip_canary(
    payload: TripRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
    _user: str = Depends(get_current_user),
):
    from app.canaries.monitor import trip_canary as trigger_trip

    source_ip = request.client.host if request.client else "0.0.0.0"
    user_agent = request.headers.get("user-agent", "")

    canary = await trigger_trip(
        token_value=payload.token_value,
        db=db,
        source_ip=source_ip,
        user_agent=user_agent,
        extra={"path": request.url.path},
    )

    if not canary:
        raise HTTPException(status_code=404, detail="Canary token not found or already tripped")

    from sqlalchemy import select
    from app.models.event import AttackEvent

    event_result = await db.execute(
        select(AttackEvent).where(AttackEvent.canary_id == canary.id).order_by(AttackEvent.timestamp.desc()).limit(1)
    )
    event = event_result.scalar_one_or_none()
    if event:
        from app.services.event_processor import process_event
        await process_event(db, event)

    # The background commit happens via get_db context manager
    # But we need immediate commit for the alert
    await db.commit()

    return {"status": "tripped", "canary_id": str(canary.id), "source_ip": source_ip}


@router.get("/{canary_id}", response_model=CanaryOut)
async def get_canary(
    canary_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    _user: str = Depends(get_current_user),
):
    result = await db.execute(select(CanaryToken).where(CanaryToken.id == canary_id))
    canary = result.scalar_one_or_none()
    if not canary:
        raise HTTPException(status_code=404, detail="Canary not found")
    return _canary_out(canary)


@router.patch("/{canary_id}", response_model=CanaryOut)
async def update_canary(
    canary_id: uuid.UUID,
    payload: CanaryUpdate,
    db: AsyncSession = Depends(get_db),
    _user: str = Depends(get_current_user),
):
    result = await db.execute(select(CanaryToken).where(CanaryToken.id == canary_id))
    canary = result.scalar_one_or_none()
    if not canary:
        raise HTTPException(status_code=404, detail="Canary not found")

    update_data = payload.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(canary, field, value)

    await db.flush()
    await db.refresh(canary)
    return _canary_out(canary)


@router.delete("/{canary_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_canary(
    canary_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    _user: str = Depends(get_current_user),
):
    result = await db.execute(select(CanaryToken).where(CanaryToken.id == canary_id))
    canary = result.scalar_one_or_none()
    if not canary:
        raise HTTPException(status_code=404, detail="Canary not found")
    await db.delete(canary)


def _canary_out(canary: CanaryToken) -> CanaryOut:
    out = CanaryOut.model_validate(canary)
    if canary.canary_type == CanaryType.URL:
        out.callback_url = f"{settings.canary_base_url.rstrip('/')}/c/{canary.token_value}"
    return out
