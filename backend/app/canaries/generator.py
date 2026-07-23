from __future__ import annotations

import uuid
import secrets
import string

from app.models.canary import CanaryType


def generate_tokens(canary_type: CanaryType, count: int = 1) -> list[str]:
    generators = {
        CanaryType.URL: _generate_url_token,
        CanaryType.DNS: _generate_dns_token,
        CanaryType.AWS_KEY: _generate_aws_token,
        CanaryType.DOCUMENT: _generate_document_token,
    }
    gen = generators.get(canary_type, _generate_url_token)
    return [gen() for _ in range(count)]


TOKEN_PREFIX = "DCPY"


def _generate_url_token() -> str:
    return f"{TOKEN_PREFIX}-{secrets.token_urlsafe(32)}"


def _generate_dns_token() -> str:
    from app.config import settings
    token = secrets.token_hex(16)
    return f"{TOKEN_PREFIX}-{token}.{settings.canary_domain}"


def _generate_aws_token() -> str:
    access_key = f"AKIA{secrets.token_hex(8).upper()}"
    return access_key


def _generate_document_token() -> str:
    return f"{TOKEN_PREFIX}-{secrets.token_urlsafe(32)}"
