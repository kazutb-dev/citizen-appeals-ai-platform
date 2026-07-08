"""Тонкий фасад над абстракцией LLMProvider для агентов MedHubHAQ.

Сохраняет прежний публичный API (``complete`` / ``complete_json``), но вся работа
с конкретной моделью вынесена в :mod:`app.agents.llm_provider`. Провайдер
(ollama / vllm) выбирается настройкой ``LLM_PROVIDER`` без изменения
бизнес-логики агентов. Используется только локальный инференс.
"""
import json
import re

from app.agents.llm_provider import get_provider


def current_model() -> str:
    """Имя активной модели (для AgentRun.model_used / логов)."""
    return get_provider().model_name


async def complete(prompt: str, *, max_tokens: int = 800, system: str | None = None) -> str:
    return await get_provider().complete(prompt, max_tokens=max_tokens, system=system)


async def complete_json(prompt: str, *, max_tokens: int = 800, system: str | None = None) -> dict:
    """Вызов модели с ответом строго в JSON; срезает возможные ```-ограждения."""
    text = await complete(prompt, max_tokens=max_tokens, system=system)
    cleaned = re.sub(r"^```(?:json)?\s*|\s*```$", "", text.strip())
    match = re.search(r"\{.*\}", cleaned, re.DOTALL)
    if match:
        cleaned = match.group(0)
    return json.loads(cleaned)
