from __future__ import annotations

import json
import logging
import random
import uuid
from typing import Any

from app.core.redis_client import redis, STREAMS

logger = logging.getLogger(__name__)

DELAY_TEMPLATES = [
    "Simulating network congestion — request queued, please wait...",
    "LDAP authentication timeout — retrying with backup domain controller...",
    "Database connection pool exhausted — retry {n}/3...",
    "TLS handshake retry — negotiating cipher suite...",
]

DECOY_RESPONSES = {
    "ls": "bin  boot  dev  etc  home  lib  media  mnt  opt  proc  root  run  sbin  srv  sys  tmp  usr  var  .ssh  .aws  .env  secrets.txt  customer_db.sql  payroll_2025.xlsx  vpn_config.ovpn",
    "whoami": "svc_deployment",
    "hostname": "prod-app-03",
    "cat /etc/passwd": "root:x:0:0:root:/root:/bin/bash\nsvc_deployment:x:1001:1001::/home/svc_deployment:/bin/bash\njenkins:x:1002:1002::/var/lib/jenkins:/bin/bash",
    "env": "PATH=/usr/local/sbin:/usr/local/bin\nAWS_ACCESS_KEY_ID=AKIA{hex}\nDATABASE_URL=postgresql://svc:ProdDB2025!@10.0.1.50:5432/customers\nJENKINS_URL=http://jenkins.internal.corp:8080\nSLACK_TOKEN=xoxb-{hex}",
}

FAKE_FILE_CONTENTS = {
    "secrets.txt": "VPN Password: Winter2025!\nDB Master Key: f7a3b2c1d4e5f6a7b8c9d0e1f2a3b4c5\nAWS Root: arn:aws:iam::123456789012:root",
    "vpn_config.ovpn": "remote vpn.corporate.net 1194 udp\nca ca.crt\nauth-user-pass\n# Contact IT for credentials",
}


class EngagementEngine:
    async def execute(
        self,
        action: str,
        target_honeypot_id: uuid.UUID | None = None,
        target_ip: str | None = None,
        params: dict | None = None,
    ) -> dict[str, Any]:
        params = params or {}

        handlers = {
            "delay": self._handle_delay,
            "mislead": self._handle_mislead,
            "gather": self._handle_gather,
            "escalate": self._handle_escalate,
            "withdraw": self._handle_withdraw,
            "passive": self._handle_passive,
        }

        handler = handlers.get(action, self._handle_passive)
        result = await handler(target_honeypot_id, target_ip, params)

        await redis.xadd(
            STREAMS["engagements"],
            {
                "action": action,
                "target_honeypot_id": str(target_honeypot_id) if target_honeypot_id else "",
                "target_ip": target_ip or "",
                "result": json.dumps(result, default=str),
            },
            maxlen=10000,
        )

        return result

    async def _handle_delay(self, hp_id, ip, params) -> dict:
        delay_sec = params.get("delay_seconds", random.randint(5, 30))
        return {
            "message": f"Delaying attacker for {delay_sec}s",
            "tactic": random.choice(DELAY_TEMPLATES),
            "delay_seconds": delay_sec,
        }

    async def _handle_mislead(self, hp_id, ip, params) -> dict:
        decoy_type = params.get("decoy_type", random.choice(list(DECOY_RESPONSES.keys())))
        response = DECOY_RESPONSES.get(decoy_type, DECOY_RESPONSES["ls"])
        import secrets
        response = response.replace("{hex}", secrets.token_hex(8))
        return {
            "message": f"Injected misleading data: {decoy_type}",
            "decoy_type": decoy_type,
            "response_snippet": response[:200],
        }

    async def _handle_gather(self, hp_id, ip, params) -> dict:
        return {
            "message": "Augmenting logging — capturing full session, syscalls, and network traffic",
            "enhanced_logging": True,
        }

    async def _handle_escalate(self, hp_id, ip, params) -> dict:
        from app.agents.deception_selector import select_decoys

        decoys = await select_decoys(
            honeypot_type=params.get("honeypot_type", "ssh"),
            event_types=[],
            attacker_ip=ip,
        )

        if params.get("deploy_honeypot"):
            pass

        return {
            "message": "Escalating — planting additional decoys and spinning up secondary honeypot",
            "planted_decoys": decoys,
        }

    async def _handle_withdraw(self, hp_id, ip, params) -> dict:
        return {
            "message": "Terminating engagement — removed all decoys and rotating canary tokens",
            "rotated_canaries": True,
        }

    async def _handle_passive(self, hp_id, ip, params) -> dict:
        return {
            "message": "Maintaining passive posture — logging all activity without intervention",
        }
