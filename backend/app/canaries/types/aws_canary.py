from __future__ import annotations


class AWSCanary:
    """Fake AWS access key that logs any API call attempt."""

    @staticmethod
    def validate_token(token: str) -> bool:
        if not token:
            return False
        return token.startswith("AKIA") and len(token) == 20

    @staticmethod
    def aws_key_details(token: str) -> dict:
        return {
            "key": token,
            "service": "AWS",
            "region": "us-east-1",
            "is_decoy": True,
        }
