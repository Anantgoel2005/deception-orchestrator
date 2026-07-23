from __future__ import annotations

import uuid
from datetime import datetime
from enum import Enum

from sqlalchemy import DateTime, Enum as SAEnum, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class HoneypotType(str, Enum):
    SSH = "ssh"
    HTTP = "http"
    DATABASE = "database"
    SMB = "smb"


class HoneypotStatus(str, Enum):
    DEPLOYING = "deploying"
    RUNNING = "running"
    PAUSED = "paused"
    STOPPED = "stopped"
    ERROR = "error"


class Honeypot(Base):
    __tablename__ = "honeypots"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    honeypot_type: Mapped[HoneypotType] = mapped_column(
        SAEnum(HoneypotType), nullable=False
    )
    status: Mapped[HoneypotStatus] = mapped_column(
        SAEnum(HoneypotStatus), default=HoneypotStatus.DEPLOYING, nullable=False
    )

    container_id: Mapped[str | None] = mapped_column(String(128), nullable=True)
    ip_address: Mapped[str | None] = mapped_column(String(45), nullable=True)
    ports: Mapped[str | None] = mapped_column(Text, nullable=True)
    config_override: Mapped[str | None] = mapped_column(Text, nullable=True)

    total_connections: Mapped[int] = mapped_column(default=0)
    total_commands: Mapped[int] = mapped_column(default=0)
    unique_attackers: Mapped[int] = mapped_column(default=0)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
