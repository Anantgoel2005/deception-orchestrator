from __future__ import annotations

import uuid
from datetime import datetime
from enum import Enum

from sqlalchemy import DateTime, Enum as SAEnum, ForeignKey, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class EventType(str, Enum):
    CONNECTION = "connection"
    LOGIN_ATTEMPT = "login_attempt"
    LOGIN_SUCCESS = "login_success"
    COMMAND = "command"
    FILE_DOWNLOAD = "file_download"
    FILE_UPLOAD = "file_upload"
    PORT_SCAN = "port_scan"
    EXPLOIT_ATTEMPT = "exploit_attempt"
    CANARY_TRIP = "canary_trip"
    SHELL_SPAWN = "shell_spawn"
    SESSION_CLOSE = "session_close"


class AttackEvent(Base):
    __tablename__ = "attack_events"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )

    honeypot_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("honeypots.id", ondelete="SET NULL"),
        nullable=True, index=True,
    )
    canary_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("canary_tokens.id", ondelete="SET NULL"),
        nullable=True, index=True,
    )

    event_type: Mapped[EventType] = mapped_column(
        SAEnum(EventType), nullable=False, index=True
    )
    source_ip: Mapped[str] = mapped_column(String(45), nullable=False, index=True)
    source_port: Mapped[int | None] = mapped_column(Integer, nullable=True)
    username: Mapped[str | None] = mapped_column(String(255), nullable=True)

    raw_log: Mapped[str | None] = mapped_column(Text, nullable=True)
    parsed_data: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    mitre_technique: Mapped[str | None] = mapped_column(String(32), nullable=True)
    mitre_tactic: Mapped[str | None] = mapped_column(String(32), nullable=True)

    threat_score: Mapped[int] = mapped_column(Integer, default=0)
    session_id: Mapped[str | None] = mapped_column(String(128), nullable=True, index=True)

    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), index=True
    )

    honeypot: Mapped["Honeypot | None"] = relationship("Honeypot", lazy="joined")
