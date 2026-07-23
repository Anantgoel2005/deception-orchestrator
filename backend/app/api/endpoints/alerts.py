from __future__ import annotations

import uuid
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_current_user, get_db
from app.models.alert import Alert, AlertSeverity, AlertStatus

router = APIRouter()


class AlertOut(BaseModel):
    id: uuid.UUID
    event_id: uuid.UUID | None
    title: str
    description: str | None
    severity: AlertSeverity
    status: AlertStatus
    recommendation: str | None
    ai_analysis: str | None
    assigned_to: str | None
    extra: dict | None
    created_at: datetime

    model_config = {"from_attributes": True}


class AlertListOut(BaseModel):
    items: list[AlertOut]
    total: int


class AlertUpdate(BaseModel):
    status: AlertStatus | None = None
    assigned_to: str | None = None
    resolved_by: str | None = None


@router.get("", response_model=AlertListOut)
async def list_alerts(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    status: AlertStatus | None = None,
    severity: AlertSeverity | None = None,
    db: AsyncSession = Depends(get_db),
    _user: str = Depends(get_current_user),
):
    conditions = []
    if status:
        conditions.append(Alert.status == status)
    if severity:
        conditions.append(Alert.severity == severity)

    total_q = select(func.count(Alert.id))
    items_q = select(Alert).order_by(Alert.created_at.desc())
    if conditions:
        total_q = total_q.where(*conditions)
        items_q = items_q.where(*conditions)

    total_result = await db.execute(total_q)
    total = total_result.scalar() or 0

    items_result = await db.execute(items_q.offset(skip).limit(limit))
    items = items_result.scalars().all()

    return AlertListOut(
        items=[AlertOut.model_validate(a) for a in items],
        total=total,
    )


@router.get("/{alert_id}", response_model=AlertOut)
async def get_alert(
    alert_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    _user: str = Depends(get_current_user),
):
    result = await db.execute(select(Alert).where(Alert.id == alert_id))
    alert = result.scalar_one_or_none()
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    return AlertOut.model_validate(alert)


@router.patch("/{alert_id}", response_model=AlertOut)
async def update_alert(
    alert_id: uuid.UUID,
    payload: AlertUpdate,
    db: AsyncSession = Depends(get_db),
    _user: str = Depends(get_current_user),
):
    result = await db.execute(select(Alert).where(Alert.id == alert_id))
    alert = result.scalar_one_or_none()
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")

    update_data = payload.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(alert, field, value)

    from datetime import timezone
    if payload.status == AlertStatus.ACKNOWLEDGED and alert.acknowledged_at is None:
        alert.acknowledged_at = datetime.now(timezone.utc)
    if payload.status == AlertStatus.RESOLVED and alert.resolved_at is None:
        alert.resolved_at = datetime.now(timezone.utc)

    await db.flush()
    await db.refresh(alert)
    return AlertOut.model_validate(alert)


@router.post("/{alert_id}/analyze", response_model=AlertOut)
async def analyze_alert(
    alert_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    _user: str = Depends(get_current_user),
):
    result = await db.execute(select(Alert).where(Alert.id == alert_id))
    alert = result.scalar_one_or_none()
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")

    from app.agents.orchestrator import analyze_alert_with_ai
    analysis = await analyze_alert_with_ai(alert)
    alert.ai_analysis = analysis

    await db.flush()
    await db.refresh(alert)
    return AlertOut.model_validate(alert)
