from __future__ import annotations

import logging
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

KNOWN_MALICIOUS_IPS: set[str] = set()
KNOWN_TOR_EXIT_NODES: set[str] = set()
KNOWN_VPN_ENDPOINTS: set[str] = set()


async def enrich_ip(ip: str) -> dict:
    result = {
        "ip": ip,
        "is_malicious": ip in KNOWN_MALICIOUS_IPS,
        "is_tor_exit": ip in KNOWN_TOR_EXIT_NODES,
        "is_vpn": ip in KNOWN_VPN_ENDPOINTS,
        "reputation": "unknown",
        "geo": {},
        "last_checked": datetime.now(timezone.utc).isoformat(),
    }

    if ip.startswith(("10.", "172.", "192.168.")) or ip == "127.0.0.1":
        result["reputation"] = "internal"
        return result

    if result["is_malicious"]:
        result["reputation"] = "malicious"
    elif result["is_tor_exit"]:
        result["reputation"] = "suspicious"

    return result


async def enrich_ioc(ioc_type: str, ioc_value: str) -> dict:
    result = {
        "type": ioc_type,
        "value": ioc_value,
        "reputation": "unknown",
        "malware_families": [],
    }

    known_hashes = {
        "md5": ["d41d8cd98f00b204e9800998ecf8427e"],
        "sha256": ["e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"],
    }
    for hash_type, values in known_hashes.items():
        if ioc_value in values:
            result["reputation"] = "malicious"
            break

    return result


def bulk_load_threat_intel(ips: list[str]) -> None:
    for ip in ips:
        KNOWN_MALICIOUS_IPS.add(ip)
