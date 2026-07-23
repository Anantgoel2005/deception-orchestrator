from __future__ import annotations

from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_current_user, get_db
from app.config import settings
from app.models.alert import Alert, AlertSeverity, AlertStatus
from app.models.canary import CanaryToken, CanaryStatus
from app.models.event import AttackEvent
from app.models.honeypot import Honeypot, HoneypotStatus

router = APIRouter()


class DashboardStats(BaseModel):
    active_honeypots: int
    total_honeypots: int
    active_canaries: int
    tripped_canaries: int
    total_events: int
    events_last_24h: int
    open_alerts: int
    critical_alerts: int
    unique_attackers_24h: int
    deployment_mode: str
    demo_mode: bool
    local_decoys_enabled: bool


@router.get("/stats", response_model=DashboardStats)
async def get_dashboard_stats(
    db: AsyncSession = Depends(get_db),
    _user: str = Depends(get_current_user),
):
    now = datetime.now(timezone.utc)
    last_24h = now - timedelta(hours=24)

    active_hp = await db.scalar(
        select(func.count(Honeypot.id)).where(Honeypot.status == HoneypotStatus.RUNNING)
    )
    total_hp = await db.scalar(select(func.count(Honeypot.id)))

    active_can = await db.scalar(
        select(func.count(CanaryToken.id)).where(CanaryToken.status == CanaryStatus.ACTIVE)
    )
    tripped_can = await db.scalar(
        select(func.count(CanaryToken.id)).where(CanaryToken.status == CanaryStatus.TRIPPED)
    )

    total_ev = await db.scalar(select(func.count(AttackEvent.id)))
    ev_24h = await db.scalar(
        select(func.count(AttackEvent.id)).where(AttackEvent.timestamp >= last_24h)
    )

    open_alerts = await db.scalar(
        select(func.count(Alert.id)).where(Alert.status.in_([AlertStatus.NEW, AlertStatus.ACKNOWLEDGED, AlertStatus.INVESTIGATING]))
    )
    critical_alerts = await db.scalar(
        select(func.count(Alert.id)).where(
            Alert.severity == AlertSeverity.CRITICAL,
            Alert.status.in_([AlertStatus.NEW, AlertStatus.ACKNOWLEDGED, AlertStatus.INVESTIGATING]),
        )
    )

    unique_ips = await db.scalar(
        select(func.count(func.distinct(AttackEvent.source_ip))).where(
            AttackEvent.timestamp >= last_24h
        )
    )

    return DashboardStats(
        active_honeypots=active_hp or 0,
        total_honeypots=total_hp or 0,
        active_canaries=active_can or 0,
        tripped_canaries=tripped_can or 0,
        total_events=total_ev or 0,
        events_last_24h=ev_24h or 0,
        open_alerts=open_alerts or 0,
        critical_alerts=critical_alerts or 0,
        unique_attackers_24h=unique_ips or 0,
        deployment_mode=settings.deployment_mode,
        demo_mode=settings.demo_mode,
        local_decoys_enabled=settings.enable_local_decoys,
    )
