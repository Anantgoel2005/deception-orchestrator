from __future__ import annotations

import logging
import random
from typing import Any

from app.models.event import EventType

logger = logging.getLogger(__name__)

DECOY_MAP = {
    "ssh": [
        {"type": "db_string", "template": "postgresql://admin:Passw0rd!@10.0.1.{ip}:5432/production"},
        {"type": "env_file", "template": "AWS_ACCESS_KEY_ID=AKIA{hex}\nAWS_SECRET_KEY={secret}"},
        {"type": "ssh_key", "template": "ssh-rsa AAAAB3NzaC1yc2E... decoy@{host}"},
    ],
    "http": [
        {"type": "api_key", "template": "Authorization: Bearer eyJhbGciOiJIUzI1NiJ9.{payload}"},
        {"type": "db_string", "template": "mongodb://admin:company{num}@internal-db:27017/customers"},
        {"type": "jwt_token", "template": "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9.{payload}"},
    ],
    "database": [
        {"type": "ssh_creds", "template": "ubuntu:ubuntu@{ip}"},
        {"type": "s3_url", "template": "s3://backups-{hex}.s3.amazonaws.com/"},
        {"type": "admin_panel", "template": "https://admin.internal.corp/login?token={hex}"},
    ],
    "smb": [
        {"type": "azure_conn", "template": "DefaultEndpointsProtocol=https;AccountName=corpstorage{num};AccountKey={hex}"},
        {"type": "aws_cli", "template": "aws s3 cp s3://financial-data-{hex}/Q4_report.pdf ./"},
        {"type": "wallet", "template": "BTC: bc1q{hex}"},
    ],
}


async def select_decoys(
    honeypot_type: str,
    event_types: list[EventType],
    attacker_ip: str | None = None,
) -> list[dict[str, Any]]:
    type_decoys = DECOY_MAP.get(honeypot_type, DECOY_MAP["ssh"])

    selected = random.sample(type_decoys, min(2, len(type_decoys)))

    result = []
    for decoy in selected:
        rendered = decoy["template"]
        rendered = rendered.replace("{ip}", str(random.randint(1, 254)))
        rendered = rendered.replace("{hex}", _random_hex(16))
        rendered = rendered.replace("{secret}", _random_hex(32))
        rendered = rendered.replace("{num}", str(random.randint(100, 999)))
        rendered = rendered.replace("{payload}", _random_hex(24))
        rendered = rendered.replace("{host}", f"decoy-{_random_hex(4)}.internal")
        result.append({
            "type": decoy["type"],
            "value": rendered,
        })

    return result


def _random_hex(length: int) -> str:
    import secrets
    return secrets.token_hex(length // 2)
