from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_current_user, get_db
from app.agents.engagement import EngagementEngine

router = APIRouter()


class EngagementAction(BaseModel):
    action: str = Field(..., description="Action to take: delay, mislead, gather, escalate, withdraw")
    target_honeypot_id: uuid.UUID | None = None
    target_ip: str | None = None
    params: dict | None = None


class EngagementResult(BaseModel):
    success: bool
    action: str
    message: str
    details: dict | None = None


@router.post("/act", response_model=EngagementResult)
async def execute_engagement(
    payload: EngagementAction,
    _user: str = Depends(get_current_user),
):
    engine = EngagementEngine()
    result = await engine.execute(
        action=payload.action,
        target_honeypot_id=payload.target_honeypot_id,
        target_ip=payload.target_ip,
        params=payload.params,
    )
    return EngagementResult(
        success=True,
        action=payload.action,
        message=result.get("message", "Action executed"),
        details=result,
    )


@router.post("/decide/{honeypot_id}", response_model=EngagementResult)
async def decide_engagement(
    honeypot_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    _user: str = Depends(get_current_user),
):
    from app.agents.orchestrator import decide_engagement_action

    action = await decide_engagement_action(honeypot_id, db)
    engine = EngagementEngine()
    result = await engine.execute(
        action=action["action"],
        target_honeypot_id=honeypot_id,
        params=action.get("params"),
    )
    return EngagementResult(
        success=True,
        action=action["action"],
        message=result.get("message", "Engagement decided and executed"),
        details=result,
    )
