from __future__ import annotations

import json
import logging
import uuid
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.llm.providers import get_llm
from app.llm.prompts import (
    ORCHESTRATOR_SYSTEM_PROMPT,
    TTP_ANALYSIS_PROMPT,
    ALERT_ANALYSIS_PROMPT,
    ENGAGEMENT_DECISION_PROMPT,
)
from app.models.event import AttackEvent
from app.models.alert import Alert

logger = logging.getLogger(__name__)


async def analyze_attack_chain(
    db: AsyncSession,
    honeypot_id: uuid.UUID | None = None,
    session_id: str | None = None,
) -> dict[str, Any]:
    conditions = []
    if honeypot_id:
        conditions.append(AttackEvent.honeypot_id == honeypot_id)
    if session_id:
        conditions.append(AttackEvent.session_id == session_id)

    query = select(AttackEvent).order_by(AttackEvent.timestamp.asc())
    if conditions:
        query = query.where(*conditions)
    result = await db.execute(query)
    events = result.scalars().all()

    if not events:
        return {"analysis": "No attack events to analyze", "techniques": [], "recommendation": "passive"}

    event_summary = []
    for e in events:
        event_summary.append({
            "type": e.event_type.value,
            "source_ip": e.source_ip,
            "username": e.username,
            "raw_log": (e.raw_log or "")[:500],
            "mitre_technique": e.mitre_technique,
            "threat_score": e.threat_score,
            "timestamp": e.timestamp.isoformat() if e.timestamp else "",
        })

    llm = get_llm()
    prompt = TTP_ANALYSIS_PROMPT.format(
        events=json.dumps(event_summary, indent=2, default=str),
    )

    try:
        response = llm.invoke(
            system_prompt=ORCHESTRATOR_SYSTEM_PROMPT,
            user_prompt=prompt,
        )
        analysis = json.loads(response)
    except (json.JSONDecodeError, Exception) as exc:
        logger.warning("LLM analysis failed, using heuristic: %s", exc)
        analysis = _heuristic_ttp_analysis(events)

    return analysis


async def analyze_alert_with_ai(alert: Alert) -> str:
    llm = get_llm()

    prompt = ALERT_ANALYSIS_PROMPT.format(
        title=alert.title,
        description=alert.description or "",
        severity=alert.severity.value,
        event_data=json.dumps(alert.extra or {}, default=str),
    )

    try:
        return llm.invoke(
            system_prompt=ORCHESTRATOR_SYSTEM_PROMPT,
            user_prompt=prompt,
        )
    except Exception as exc:
        logger.warning("LLM alert analysis failed: %s", exc)
        return f"Automated analysis unavailable. Recommend manual investigation of {alert.severity.value} severity alert: {alert.title}"


async def decide_engagement_action(
    honeypot_id: uuid.UUID,
    db: AsyncSession,
) -> dict[str, Any]:
    analysis = await analyze_attack_chain(db, honeypot_id=honeypot_id)

    llm = get_llm()
    prompt = ENGAGEMENT_DECISION_PROMPT.format(
        analysis=json.dumps(analysis, indent=2),
    )

    try:
        response = llm.invoke(
            system_prompt=ORCHESTRATOR_SYSTEM_PROMPT,
            user_prompt=prompt,
        )
        decision = json.loads(response)
    except (json.JSONDecodeError, Exception) as exc:
        logger.warning("LLM engagement decision failed: %s", exc)
        decision = {"action": "passive", "reason": "Falling back to passive monitoring", "params": {}}

    return decision


def _heuristic_ttp_analysis(events: list[AttackEvent]) -> dict[str, Any]:
    techniques = set()
    threat_score = 0
    has_login = False
    has_command = False
    has_exploit = False

    for e in events:
        threat_score += e.threat_score
        if e.mitre_technique:
            techniques.add(e.mitre_technique)
        if e.event_type.value == "login_success":
            has_login = True
        if e.event_type.value == "command":
            has_command = True
        if e.event_type.value == "exploit_attempt":
            has_exploit = True

    recommendation = "passive"
    if has_exploit:
        recommendation = "isolate_and_gather"
    elif has_login and has_command:
        recommendation = "delay_and_mislead"
    elif has_login:
        recommendation = "monitor_and_log"

    return {
        "techniques": list(techniques),
        "threat_score": threat_score,
        "has_login": has_login,
        "has_command_execution": has_command,
        "has_exploit": has_exploit,
        "recommendation": recommendation,
        "event_count": len(events),
    }
