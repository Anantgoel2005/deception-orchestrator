from __future__ import annotations

import asyncio
import logging
import re
from sqlalchemy import select

from app.core.database import async_session_factory
from app.core.docker_client import get_docker
from app.core.redis_client import redis, STREAMS
from app.models.event import AttackEvent, EventType
from app.models.canary import CanaryToken  # noqa: F401 - register metadata for worker-only imports
from app.models.honeypot import Honeypot, HoneypotStatus

logger = logging.getLogger(__name__)

# Patterns for extracting events from SSH logs
SSH_PATTERNS: list[tuple[re.Pattern, str, str]] = [
    (re.compile(r"Accepted (\w+) for (\S+) from (\S+) port (\d+)"), "login_success", "Accepted {method} for {user} from {ip} port {port}"),
    (re.compile(r"Failed (\w+) for (\S+) from (\S+) port (\d+)"), "login_attempt", "Failed {method} for {user} from {ip} port {port}"),
    (re.compile(r"Connection closed by (\S+) port (\d+)"), "session_close", "Connection closed by {ip} port {port}"),
    (re.compile(r"Connection from (\S+) port (\d+)"), "connection", "Connection from {ip} port {port}"),
]


async def monitor_honeypot_logs() -> None:
    try:
        docker_client = get_docker()
    except RuntimeError:
        logger.warning("Docker unavailable — log monitor disabled")
        return

    logger.info("Honeypot log monitor started")
    tracked: dict[str, str] = {}

    while True:
        try:
            async with async_session_factory() as session:
                result = await session.execute(
                    select(Honeypot.container_id, Honeypot.id).where(
                        Honeypot.status == HoneypotStatus.RUNNING,
                        Honeypot.container_id.is_not(None),
                    )
                )
                for row in result.all():
                    container_id = str(row[0])
                    honeypot_id = str(row[1])

                    if container_id not in tracked:
                        tracked[container_id] = honeypot_id
                        logger.info("Now tracking honeypot %s (container %s)", honeypot_id, container_id[:12])

                    try:
                        container = docker_client.containers.get(container_id)
                        logs = container.logs(tail=20, timestamps=True).decode("utf-8", errors="replace")

                        for line in logs.strip().split("\n"):
                            if not line.strip():
                                continue
                            await _process_log_line(session, honeypot_id, line, container_id)
                    except Exception as exc:
                        logger.warning("Failed to process logs for %s: %s", container_id[:12], exc)

                await session.commit()
        except Exception as exc:
            logger.debug("Log monitor cycle error: %s", exc)

        await asyncio.sleep(5)


async def _process_log_line(session, honeypot_id: str, line: str, container_id: str) -> None:
    import uuid

    log_key = f"lp:{container_id}:{hash(line)}"
    try:
        if await redis.get(log_key):
            return
        await redis.set(log_key, "1", ex=300)
    except Exception as exc:
        logger.debug("Redis deduplication unavailable: %s", exc)

    clean_line = _strip_timestamp(line)
    source_ip = "0.0.0.0"
    event_type = EventType.COMMAND

    for pattern, evt_type, _ in SSH_PATTERNS:
        match = pattern.search(clean_line)
        if match:
            event_type = EventType(evt_type)
            ip_match = match.group(3) if match.lastindex and match.lastindex >= 3 else match.group(1)
            source_ip = ip_match if re.match(r"\d+\.\d+\.\d+\.\d+", ip_match) else "0.0.0.0"
            break

    if "error" in clean_line.lower() or "invalid" in clean_line.lower():
        source_ip = re.findall(r"(\d+\.\d+\.\d+\.\d+)", clean_line)
        source_ip = source_ip[-1] if source_ip else "0.0.0.0"

    event = AttackEvent(
        honeypot_id=uuid.UUID(honeypot_id),
        event_type=event_type,
        source_ip=source_ip,
        raw_log=clean_line[:2000],
        parsed_data={"container_id": container_id},
    )
    session.add(event)
    await session.flush()

    from app.services.event_processor import process_event
    await process_event(session, event)

    try:
        await redis.xadd(
            STREAMS["events"],
            {"event_id": str(event.id), "event_type": event.event_type.value, "source_ip": event.source_ip, "timestamp": ""},
            maxlen=50000,
        )
    except Exception as exc:
        logger.debug("Redis stream unavailable: %s", exc)


def _strip_timestamp(line: str) -> str:
    ts_match = re.match(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}[.\d+Z]*\s+", line)
    if ts_match:
        return line[ts_match.end():]
    return line
