"""Агент 1: приоритизация обращений (эскалация руководству медорганизации).

Выявляет критичные обращения — угрозы жизни и здоровью пациентов, летальные
исходы, врачебная халатность, отказ в госпитализации/лечении, отсутствие
жизненно важных лекарств, вспышки инфекций, коррупция (поборы) и нарушения
прав пациентов — и эскалирует руководству (главный врач / заместитель /
заведующий отделением).
"""
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.agents import agent_config
from app.agents.llm_client import complete_json
from app.models.appeal import Appeal

# Словари ключевых слов для быстрой предварительной проверки.
# Переопределяются из админ-панели через agent_settings.config["keywords"].
CRITICAL_KEYWORDS = {
    "patient_safety": [
        "смерть", "умер", "умерла", "скончал", "летальный исход", "погиб",
        "угроза жизни", "реанимац", "критическое состояние", "клиническая смерть",
        "тяжёлое состояние", "суицид", "не хочу жить",
    ],
    "care_refusal": [
        "отказали в помощи", "отказ в госпитализации", "не приняли",
        "не оказали помощь", "отказали в лечении", "выгнали из больницы",
        "не госпитализировали", "отказали в приёме",
    ],
    "medicine": [
        "нет лекарств", "отсутствуют лекарства", "нет инсулина", "нет вакцины",
        "нет препарата", "закончились лекарства", "не выдают лекарства",
    ],
    "emergency": [
        "скорая не приехала", "скорая не едет", "ждём скорую", "вспышка",
        "инфекция", "заражение", "эпидемия", "массовое отравление", "отравление",
    ],
    "corruption": [
        "взятка", "взятку", "вымогательство", "вымогают", "поборы",
        "требуют деньги", "платить за бесплатное", "неофициально",
    ],
    "negligence": [
        "халатность", "врачебная ошибка", "неправильный диагноз", "залечили",
        "по вине врача", "изувечили", "занесли инфекцию",
    ],
}

CRITICAL_LLM_PROMPT = """
Ты — аналитик системы обращений граждан в сфере здравоохранения (MedHubHAQ).
Оцени обращение пациента на предмет необходимости эскалации руководству
медицинской организации.

Твоя задача: определить уровень критичности по риску для жизни и здоровья,
резонансности (соцсети), массовости и системности.

ПРАВИЛА КЛАССИФИКАЦИИ:
- "critical": угроза жизни/здоровью пациента, летальный исход, отказ в экстренной помощи или госпитализации, отсутствие жизненно важных лекарств, вспышка инфекции, суицидальные/кризисные маркеры → эскалация до chief_doctor
- "high": врачебная халатность/ошибка, коррупция (поборы за бесплатную помощь), грубое нарушение прав пациента, репутационные угрозы (СМИ, массовые жалобы) → эскалация до deputy_chief
- "medium": системные проблемы отделения/подразделения, требующие внимания руководства → эскалация до head_of_department либо без эскалации
- "low": стандартные обращения (запись, справки, бытовые вопросы)

ОБРАЩЕНИЕ:
---
{appeal_text}
---

РЕГИОН: {region}
КАТЕГОРИЯ: {category}
ТИП ЗАЯВИТЕЛЯ: {requester_type}

Ответь СТРОГО в JSON формате (без markdown, без пояснений):
{{
    "risk_level": "critical|high|medium|low",
    "risk_score": 0.0,
    "risk_reasons": ["причина 1 на русском", "причина 2 на русском"],
    "escalate": true,
    "escalation_level": "chief_doctor|deputy_chief|head_of_department|none",
    "escalation_reason": "объяснение на русском или null",
    "tags": ["тег1", "тег2"],
    "requires_immediate_action": true,
    "summary": "Краткое описание сути обращения (1-2 предложения)"
}}
"""


class CriticalResult(BaseModel):
    risk_level: str = "low"
    risk_score: float = 0.0
    risk_reasons: list[str] = Field(default_factory=list)
    escalate: bool = False
    escalation_level: str | None = None
    escalation_reason: str | None = None
    tags: list[str] = Field(default_factory=list)
    requires_immediate_action: bool = False
    summary: str = ""


async def analyze(appeal: Appeal, db: AsyncSession) -> CriticalResult:
    config = await agent_config.get_config(
        db, "agent1", {"keywords": CRITICAL_KEYWORDS, "auto_escalate_types": ["patient_safety", "emergency", "care_refusal", "medicine"]}
    )
    keywords: dict[str, list[str]] = config["keywords"]
    auto_escalate: list[str] = config["auto_escalate_types"]

    # 1. Быстрая проверка по ключевым словам
    text_lower = appeal.text.lower()
    keyword_triggers = []
    for risk_type, words in keywords.items():
        for kw in words:
            if kw in text_lower:
                keyword_triggers.append(risk_type)
                break

    # 2. Критичные триггеры (безопасность, ЧС) → сразу critical без LLM (быстрее)
    if any(t in keyword_triggers for t in auto_escalate):
        return CriticalResult(
            risk_level="critical",
            risk_score=0.95,
            risk_reasons=[
                "Обнаружены ключевые слова, указывающие на угрозу жизни/здоровью или медицинскую ЧС"
            ],
            escalate=True,
            escalation_level="chief_doctor",
            escalation_reason="Автоматическая эскалация по критичным ключевым словам",
            tags=keyword_triggers,
            requires_immediate_action=True,
            summary="Критичное обращение, требует немедленной реакции",
        )

    # 3. LLM анализ для всех остальных
    prompt = await agent_config.get_prompt(db, "agent1", CRITICAL_LLM_PROMPT)
    result_json = await complete_json(
        prompt.format(
            appeal_text=appeal.text[:2000],
            region=appeal.region,
            category=appeal.category,
            requester_type=(
                appeal.requester.requester_type if appeal.requester else "не указан"
            ),
        ),
        max_tokens=500,
    )
    if result_json.get("escalation_level") == "none":
        result_json["escalation_level"] = None
    result = CriticalResult(**result_json)
    # Ключевые слова из быстрой проверки добавляем в теги
    result.tags = list(dict.fromkeys(result.tags + keyword_triggers))
    return result
