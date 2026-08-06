from __future__ import annotations

from pathlib import Path
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        # Local development uses the repository .env; containers receive the
        # same values as environment variables from Compose.
        env_file=Path(__file__).resolve().parents[2] / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # ── Database ──
    database_url: str = "postgresql+asyncpg://decoy:decoy@localhost:5432/deception_db"

    # ── Redis ──
    redis_url: str = "redis://localhost:6379/0"

    # ── Auth ──
    secret_key: str = ""
    jwt_algorithm: Literal["HS256"] = "HS256"
    jwt_issuer: str = "deception-orchestrator"
    jwt_audience: str = "deception-orchestrator-console"

    # ── LLM ──
    openai_api_key: str = ""
    deepseek_api_key: str = ""
    llm_provider: Literal["openai", "deepseek", "offline"] = "deepseek"
    llm_model: str = "deepseek-v4-flash"

    # ── Product / security ──
    deployment_mode: Literal["development", "production"] = "development"
    app_base_url: str = "http://localhost:3000"
    canary_base_url: str = "http://localhost:8000"
    admin_username: str = "admin"
    admin_password_hash: str = ""
    admin_password: str = ""
    session_expire_minutes: int = 120
    demo_mode: bool = True
    enable_local_decoys: bool = False
    event_retention_days: int = 30

    # ── Docker ──
    docker_host: str = "npipe:////./pipe/docker_engine"

    # ── Honeypot Network ──
    honeypot_subnet: str = "172.28.0.0/16"
    honeypot_gateway: str = "172.28.0.1"

    # ── Canary ──
    canary_domain: str = "deception-monitor.example.com"

    # ── Alerting ──
    slack_webhook_url: str = ""
    smtp_host: str = ""
    smtp_port: int = 587
    smtp_user: str = ""
    smtp_password: str = ""
    alert_from_email: str = "deception@example.com"

    # ── Server ──
    host: str = "0.0.0.0"
    port: int = 8000
    debug: bool = False
    cors_origins: list[str] = ["http://localhost:3000"]

    def validate_runtime(self) -> None:
        """Reject configurations that would create an unsafe control plane."""
        errors = []
        if len(self.secret_key) < 32:
            errors.append("SECRET_KEY (at least 32 characters)")
        if not self.admin_password_hash and not self.admin_password:
            errors.append("ADMIN_PASSWORD_HASH or development ADMIN_PASSWORD")
        if self.session_expire_minutes < 5 or self.session_expire_minutes > 1440:
            errors.append("SESSION_EXPIRE_MINUTES (between 5 and 1440)")
        if self.event_retention_days < 1:
            errors.append("EVENT_RETENTION_DAYS (at least 1)")

        if self.deployment_mode != "production":
            if errors:
                raise RuntimeError("Unsafe runtime configuration: " + ", ".join(errors))
            return
        if self.admin_password:
            errors.append("ADMIN_PASSWORD must not be used in production")
        if not self.admin_password_hash:
            errors.append("ADMIN_PASSWORD_HASH")
        if not self.app_base_url.startswith("https://"):
            errors.append("APP_BASE_URL (https)")
        if not self.canary_base_url.startswith("https://"):
            errors.append("CANARY_BASE_URL (https)")
        if not self.cors_origins or "*" in self.cors_origins:
            errors.append("CORS_ORIGINS (explicit origins only)")
        if errors:
            raise RuntimeError("Unsafe production configuration: " + ", ".join(dict.fromkeys(errors)))


settings = Settings()
