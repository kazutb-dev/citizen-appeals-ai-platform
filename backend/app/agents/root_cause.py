"""AI Root Cause Analysis — определяет вероятные первопричины по кластеру/категории.

Вместо простого показа обращений строит гипотезы о корневых причинах (например:
дефицит лекарств → задержка поставщика / бюджет / несоответствие остатков) на
основе РЕАЛЬНЫХ текстов обращений. Структурированный JSON-вывод локального LLM.
"""
from pydantic import BaseModel, Field

from app.agents.llm_client import complete_json

ROOT_CAUSE_SYSTEM = (
    "Ты — аналитик первопричин в системе обращений граждан в сфере здравоохранения "
    "(MedHubHAQ). Определяешь корневые причины проблем, а не симптомы. Отвечаешь "
    "строго в JSON, на русском, опираясь только на приведённые обращения."
)

ROOT_CAUSE_PROMPT = """Проанализируй выборку обращений граждан по направлению
«{category_label}» и определи вероятные КОРНЕВЫЕ причины (root causes), а не
поверхностные симптомы.

ВЫБОРКА ОБРАЩЕНИЙ (до 12):
{samples}

Верни СТРОГО JSON:
{{
  "summary": "1-2 предложения о сути проблемы",
  "root_causes": [
    {{"cause": "корневая причина", "likelihood": 0.0, "evidence": "на что опирается вывод"}}
  ],
  "recommended_actions": ["действие 1", "действие 2"]
}}
Не выдумывай фактов сверх приведённых обращений."""


class RootCause(BaseModel):
    cause: str
    likelihood: float = 0.0
    evidence: str = ""


class RootCauseReport(BaseModel):
    category: str
    category_label: str
    sample_size: int
    summary: str = ""
    root_causes: list[RootCause] = Field(default_factory=list)
    recommended_actions: list[str] = Field(default_factory=list)
    ai_available: bool = True


async def analyze_root_cause(
    category: str, category_label: str, sample_texts: list[str]
) -> RootCauseReport:
    samples = "\n---\n".join(t[:600] for t in sample_texts[:12]) or "(нет обращений)"
    data = await complete_json(
        ROOT_CAUSE_PROMPT.format(category_label=category_label, samples=samples),
        max_tokens=700,
        system=ROOT_CAUSE_SYSTEM,
    )
    causes = [RootCause(**c) for c in data.get("root_causes", []) if isinstance(c, dict)]
    return RootCauseReport(
        category=category,
        category_label=category_label,
        sample_size=len(sample_texts),
        summary=data.get("summary", ""),
        root_causes=causes,
        recommended_actions=data.get("recommended_actions", []),
    )
