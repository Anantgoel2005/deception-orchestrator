from __future__ import annotations


class URLCanary:
    """URL token that alerts when fetched. Plant in emails, web pages, config files."""

    @staticmethod
    def validate_token(token: str) -> bool:
        return token.startswith("DCPY-") if token else False

    @staticmethod
    def extract_token_from_url(url: str) -> str | None:
        parts = url.split("/t/")
        return parts[-1] if len(parts) > 1 else None
