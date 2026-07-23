from __future__ import annotations

import json
import logging
from datetime import datetime, timezone

from app.llm.providers import get_llm
from app.llm.prompts import INCIDENT_REPORT_PROMPT

logger = logging.getLogger(__name__)


async def generate_incident_report(
    events: list,
    alerts: list,
    title: str = "Deception Incident Report",
) -> str:
    event_data = []
    for e in events:
        event_data.append({
            "type": e.event_type.value if hasattr(e.event_type, "value") else str(e.event_type),
            "source_ip": e.source_ip,
            "username": getattr(e, "username", None),
            "raw_log": (getattr(e, "raw_log", "") or "")[:1000],
            "mitre_technique": getattr(e, "mitre_technique", None),
            "timestamp": e.timestamp.isoformat() if hasattr(e, "timestamp") and e.timestamp else "",
        })

    alert_data = []
    for a in alerts:
        alert_data.append({
            "title": a.title,
            "severity": a.severity.value if hasattr(a.severity, "value") else str(a.severity),
            "description": a.description or "",
        })

    prompt = INCIDENT_REPORT_PROMPT.format(
        title=title,
        generated_at=datetime.now(timezone.utc).isoformat(),
        events=json.dumps(event_data, indent=2, default=str),
        alerts=json.dumps(alert_data, indent=2, default=str),
    )

    llm = get_llm()
    try:
        return llm.invoke(
            user_prompt=prompt,
        )
    except Exception as exc:
        logger.warning("LLM report generation failed: %s", exc)
        return _fallback_report(event_data, alert_data, title)


def _fallback_report(events: list, alerts: list, title: str) -> str:
    report = f"# {title}\n\n"
    report += f"**Generated:** {datetime.now(timezone.utc).isoformat()}\n\n"
    report += "## Summary\n\n"

    if events:
        ips = {e.get("source_ip") for e in events if e.get("source_ip")}
        report += f"- **Attackers:** {len(ips)} unique IPs ({', '.join(ips)})\n"
        report += f"- **Events:** {len(events)}\n"
    if alerts:
        report += f"- **Alerts:** {len(alerts)}\n"

    report += "\n## Attack Timeline\n\n"
    for e in events:
        ts = e.get("timestamp", "unknown")
        etype = e.get("type", "unknown")
        ip = e.get("source_ip", "unknown")
        report += f"- `{ts}` - **{etype}** from `{ip}`\n"
        if e.get("raw_log"):
            report += f"  ```\n  {e['raw_log'][:200]}\n  ```\n"

    return report
