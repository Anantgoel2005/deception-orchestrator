from __future__ import annotations

from app.config import settings


class DocumentCanary:
    """Document token (PDF/DOCX) that phones home when opened.
    Embed an invisible web beacon or macro that triggers a callback."""

    @staticmethod
    def validate_token(token: str) -> bool:
        return token.startswith("DCPY-") if token else False

    @staticmethod
    def generate_beacon_html(token: str) -> str:
        return (
            f'<img src="https://{settings.canary_domain}/d/'
            f'{token}" width="1" height="1" style="display:none" />'
        )
