from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from typing import Any

from app.config import settings

logger = logging.getLogger(__name__)


class LLMProvider(ABC):
    @abstractmethod
    def invoke(
        self,
        user_prompt: str,
        system_prompt: str = "",
        temperature: float = 0.3,
        max_tokens: int = 2048,
    ) -> str:
        ...


class OfflineProvider(LLMProvider):
    def invoke(self, user_prompt: str, system_prompt: str = "", temperature: float = 0.3, max_tokens: int = 2048) -> str:
        logger.info("Offline LLM: returning structured default response")
        if "MITRE" in user_prompt or "TTP" in user_prompt:
            return '{"technique_id": "T1059", "technique_name": "Command and Scripting Interpreter", "tactic": "Execution", "confidence": 0.5}'
        if "engagement" in user_prompt.lower() or "should I" in user_prompt.lower():
            return '{"action": "passive", "reason": "Offline mode — defaulting to passive monitoring", "params": {}}'
        if "incident report" in user_prompt.lower():
            return "[Offline mode] Auto-generated incident report. Review events manually for full analysis."
        return "[Offline LLM] Analysis unavailable. Set LLM_PROVIDER=openai and provide OPENAI_API_KEY."


class OpenAIProvider(LLMProvider):
    def __init__(self) -> None:
        from openai import OpenAI
        self._client = OpenAI(api_key=settings.openai_api_key)

    def invoke(self, user_prompt: str, system_prompt: str = "", temperature: float = 0.3, max_tokens: int = 2048) -> str:
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": user_prompt})

        response = self._client.chat.completions.create(
            model=settings.llm_model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
        )
        return response.choices[0].message.content or ""


class DeepSeekProvider(LLMProvider):
    def __init__(self) -> None:
        from openai import OpenAI
        self._client = OpenAI(
            api_key=settings.deepseek_api_key,
            base_url="https://api.deepseek.com",
        )

    def invoke(self, user_prompt: str, system_prompt: str = "", temperature: float = 0.3, max_tokens: int = 2048) -> str:
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": user_prompt})

        response = self._client.chat.completions.create(
            model=settings.llm_model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
        )
        return response.choices[0].message.content or ""


_provider: LLMProvider | None = None


def get_llm() -> LLMProvider:
    global _provider
    if _provider is None:
        if settings.llm_provider == "openai" and settings.openai_api_key:
            _provider = OpenAIProvider()
            logger.info("LLM: using OpenAI (%s)", settings.llm_model)
        elif settings.llm_provider == "deepseek" and settings.deepseek_api_key:
            _provider = DeepSeekProvider()
            logger.info("LLM: using DeepSeek (%s)", settings.llm_model)
        else:
            logger.info("LLM: using offline (simulated) provider")
            _provider = OfflineProvider()
    return _provider
