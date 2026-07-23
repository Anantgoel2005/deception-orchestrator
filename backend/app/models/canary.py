from __future__ import annotations

import uuid
from datetime import datetime
from enum import Enum

from sqlalchemy import DateTime, Enum as SAEnum, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class CanaryType(str, Enum):
    URL = "url"
    DNS = "dns"
    AWS_KEY = "aws_key"
    DOCUMENT = "document"


class CanaryStatus(str, Enum):
    ACTIVE = "active"
    TRIPPED = "tripped"
    REVOKED = "revoked"
    EXPIRED = "expired"


class CanaryToken(Base):
    __tablename__ = "canary_tokens"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    canary_type: Mapped[CanaryType] = mapped_column(
        SAEnum(CanaryType), nullable=False
    )
    status: Mapped[CanaryStatus] = mapped_column(
        SAEnum(CanaryStatus), default=CanaryStatus.ACTIVE, nullable=False
    )

    token_value: Mapped[str] = mapped_column(String(2048), nullable=False, unique=True)
    token_metadata: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    planted_location: Mapped[str | None] = mapped_column(String(1024), nullable=True)

    tripped_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    trip_source_ip: Mapped[str | None] = mapped_column(String(45), nullable=True)
    trip_user_agent: Mapped[str | None] = mapped_column(Text, nullable=True)
    trip_extra: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    expires_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
