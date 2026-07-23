from __future__ import annotations

import json
import logging
import re
import json

from app.llm.providers import get_llm
from app.llm.prompts import MITRE_MAPPING_PROMPT
from app.utils.mitre import MITRE_TECHNIQUE_LOOKUP

logger = logging.getLogger(__name__)


async def classify_ttp(command_line: str, raw_log: str) -> dict:
    llm = get_llm()

    prompt = MITRE_MAPPING_PROMPT.format(
        command=command_line[:1000],
        log=raw_log[:2000],
    )

    try:
        response = llm.invoke(user_prompt=prompt)
        result = json.loads(response)
    except (json.JSONDecodeError, Exception) as exc:
        logger.debug("LLM TTP classification failed, using regex fallback: %s", exc)
        result = _regex_ttp_fallback(command_line, raw_log)

    return result


def _regex_ttp_fallback(command_line: str, raw_log: str) -> dict:
    combined = (command_line + " " + raw_log).lower()

    patterns = {
        "T1059": r"\b(bash|sh |cmd|powershell|python |perl |ruby )\b",
        "T1003": r"\b(mimikatz|lsass|procdump|secretsdump)\b",
        "T1078": r"\b(ssh |scp |rsync)\b",
        "T1505.003": r"\b(http|https|curl |wget |\.php)\b",
        "T1046": r"\b(nmap|masscan|scan\b)",
        "T1110": r"\b(password|passwd|brute|hydra|medusa)\b",
        "T1021.001": r"\b(rdp |remote desktop)\b",
        "T1570": r"\b(tftp|nc |netcat|upload|download)\b",
        "T1105": r"\b(file.+transfer|ingress tool)\b",
        "T1560": r"\b(zip|tar|gzip|7z|archive)\b",
    }

    for technique_id, pattern in patterns.items():
        if re.search(pattern, combined):
            t = MITRE_TECHNIQUE_LOOKUP.get(technique_id, {})
            return {
                "technique_id": technique_id,
                "technique_name": t.get("name", "Unknown"),
                "tactic": t.get("tactic", "Unknown"),
                "confidence": 0.6,
            }

    return {
        "technique_id": "T1201",
        "technique_name": MITRE_TECHNIQUE_LOOKUP.get("T1201", {}).get("name", "Unknown"),
        "tactic": MITRE_TECHNIQUE_LOOKUP.get("T1201", {}).get("tactic", "Credential Access"),
        "confidence": 0.3,
    }
