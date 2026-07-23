from __future__ import annotations


class DNSCanary:
    """DNS token that alerts on resolution. Plant as domain references in configs."""

    @staticmethod
    def validate_token(token: str) -> bool:
        return "DCPY-" in token if token else False

    @staticmethod
    def extract_token_from_dns(query: str) -> str | None:
        parts = query.split(".")
        for part in parts:
            if part.startswith("DCPY-"):
                return part
        return None
