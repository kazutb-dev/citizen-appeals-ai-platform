"""Абстракция провайдера LLM для агентов MedHubHAQ.

Бизнес-логика агентов не зависит от конкретного бэкенда модели. Используется
ТОЛЬКО локальный инференс — данные не покидают инфраструктуру государства.
Провайдер выбирается через настройку ``LLM_PROVIDER``:

* ``ollama`` — локальный self-hosted инференс через Ollama;
* ``vllm``   — локальный OpenAI-совместимый сервер (vLLM или llama.cpp server).

Облачные API (OpenAI / Anthropic / Gemini / DeepSeek) запрещены и не поддерживаются.
Чтобы сменить модель, достаточно изменить переменные окружения
(``LLM_PROVIDER``, ``LLM_BASE_URL``, ``LLM_LOCAL_MODEL``) — код агентов не меняется.
"""
from __future__ import annotations

from abc import ABC, abstractmethod

import httpx

from app.config import settings

# Локальный self-hosted инференс 8B-модели может генерировать длинные ответы
# (официальные ответы Агента 4, казахский язык — медленнее), поэтому read-timeout
# берётся с запасом; connect-timeout остаётся коротким.
_DEFAULT_TIMEOUT = httpx.Timeout(180.0, connect=10.0)


class LLMProvider(ABC):
    """Единый интерфейс генерации текста для всех агентов."""

    #: человекочитаемое имя используемой модели (для логов/AgentRun.model_used)
    model_name: str

    @abstractmethod
    async def complete(self, prompt: str, *, max_tokens: int = 800, system: str | None = None) -> str:
        """Сгенерировать ответ модели в виде простого текста."""
        raise NotImplementedError


class OllamaProvider(LLMProvider):
    """Локальный self-hosted инференс через Ollama (research deployment)."""

    def __init__(self) -> None:
        if not settings.LLM_BASE_URL:
            raise RuntimeError("LLM_BASE_URL не задан — провайдер ollama недоступен.")
        if not settings.LLM_LOCAL_MODEL:
            raise RuntimeError("LLM_LOCAL_MODEL не задан — укажите имя локальной модели.")
        self._base_url = settings.LLM_BASE_URL.rstrip("/")
        self.model_name = settings.LLM_LOCAL_MODEL

    async def complete(self, prompt: str, *, max_tokens: int = 800, system: str | None = None) -> str:
        payload: dict = {
            "model": self.model_name,
            "prompt": prompt,
            "stream": False,
            # Для think-моделей (например, qwen3) просим финальный текстовый ответ,
            # иначе часть серверов возвращает пустой `response` и только `thinking`.
            "think": False,
            "options": {"num_predict": max_tokens},
        }
        if system:
            payload["system"] = system
        async with httpx.AsyncClient(timeout=_DEFAULT_TIMEOUT) as client:
            resp = await client.post(f"{self._base_url}/api/generate", json=payload)
            resp.raise_for_status()
            return resp.json()["response"]


class VLLMProvider(LLMProvider):
    """Локальный OpenAI-совместимый сервер vLLM (research deployment)."""

    def __init__(self) -> None:
        if not settings.LLM_BASE_URL:
            raise RuntimeError("LLM_BASE_URL не задан — провайдер vllm недоступен.")
        if not settings.LLM_LOCAL_MODEL:
            raise RuntimeError("LLM_LOCAL_MODEL не задан — укажите имя локальной модели.")
        self._base_url = settings.LLM_BASE_URL.rstrip("/")
        self.model_name = settings.LLM_LOCAL_MODEL

    async def complete(self, prompt: str, *, max_tokens: int = 800, system: str | None = None) -> str:
        messages: list[dict] = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})
        payload = {
            "model": self.model_name,
            "messages": messages,
            "max_tokens": max_tokens,
            "stream": False,
        }
        async with httpx.AsyncClient(timeout=_DEFAULT_TIMEOUT) as client:
            resp = await client.post(f"{self._base_url}/v1/chat/completions", json=payload)
            resp.raise_for_status()
            return resp.json()["choices"][0]["message"]["content"]


_PROVIDERS: dict[str, type[LLMProvider]] = {
    "ollama": OllamaProvider,
    "vllm": VLLMProvider,
}

_provider: LLMProvider | None = None


def get_provider() -> LLMProvider:
    """Ленивая инициализация провайдера согласно настройке LLM_PROVIDER."""
    global _provider
    if _provider is None:
        key = (settings.LLM_PROVIDER or "ollama").lower()
        if key not in _PROVIDERS:
            raise RuntimeError(
                f"Неизвестный LLM_PROVIDER='{key}'. Допустимо: {', '.join(_PROVIDERS)}."
            )
        _provider = _PROVIDERS[key]()
    return _provider


def reset_provider() -> None:
    """Сбросить кэш провайдера (для тестов/смены конфигурации в рантайме)."""
    global _provider
    _provider = None
