"""Профильные медицинские агенты (6–8): лекарственное обеспечение, качество
медицинской помощи, санитарно-эпидемиологический контроль.

Это детерминированные правило-ориентированные классификаторы (без LLM): они
анализируют текст и категорию обращения, выставляют флаги и рекомендуют
маршрутизацию в профильное подразделение. Запускаются в фоновом воркере
оркестратором после основных пяти агентов.
"""
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.agents import agent_config
from app.models.appeal import Appeal


def _hits(text: str, words: list[str]) -> list[str]:
    t = (text or "").lower()
    return [w for w in words if w in t]


# ============================================================
# Агент 6 — лекарственное обеспечение (→ Аптека)
# ============================================================

MEDICINE_KEYWORDS = [
    "нет лекарств", "отсутствуют лекарства", "нет препарата", "нет инсулина",
    "нет вакцины", "закончились лекарства", "не выдают лекарства", "льготные лекарства",
    "бесплатные лекарства", "рецепт", "препарат отсутствует", "в аптеке нет",
]


class MedicineSupplyResult(BaseModel):
    flagged: bool = False
    confidence: float = 0.0
    signals: list[str] = Field(default_factory=list)
    route_to: str | None = None
    note: str | None = None


async def medicine_supply_analyze(appeal: Appeal, db: AsyncSession) -> MedicineSupplyResult:
    config = await agent_config.get_config(db, "agent6", {"keywords": MEDICINE_KEYWORDS})
    hits = _hits(appeal.text, config["keywords"])
    flagged = bool(hits) or appeal.category == "medicines"
    if not flagged:
        return MedicineSupplyResult()
    return MedicineSupplyResult(
        flagged=True,
        confidence=min(0.95, 0.6 + 0.1 * len(hits)),
        signals=hits or ["category=medicines"],
        route_to="PHARMACY",
        note="Признаки проблем лекарственного обеспечения — направить в аптеку "
        "и службу лекарственного обеспечения для проверки наличия и льгот.",
    )


# ============================================================
# Агент 7 — качество медицинской помощи (→ Служба качества)
# ============================================================

CARE_QUALITY_KEYWORDS = [
    "врачебная ошибка", "халатность", "неправильный диагноз", "неправильно лечили",
    "грубость", "нахамил", "нахамили", "некомпетентн", "не осмотрел",
    "неправильное лечение", "осложнени", "залечили", "равнодушие", "отказали в помощи",
]


class CareQualityResult(BaseModel):
    flagged: bool = False
    confidence: float = 0.0
    signals: list[str] = Field(default_factory=list)
    route_to: str | None = None
    note: str | None = None


async def care_quality_analyze(appeal: Appeal, db: AsyncSession) -> CareQualityResult:
    config = await agent_config.get_config(db, "agent7", {"keywords": CARE_QUALITY_KEYWORDS})
    hits = _hits(appeal.text, config["keywords"])
    flagged = bool(hits) or appeal.category in ("quality_of_care", "medical_staff")
    if not flagged:
        return CareQualityResult()
    return CareQualityResult(
        flagged=True,
        confidence=min(0.9, 0.55 + 0.1 * len(hits)),
        signals=hits or ["category=quality_of_care"],
        route_to="QUALITY",
        note="Жалоба на качество медицинской помощи или работу персонала — "
        "направить в службу поддержки пациентов и качества медпомощи для экспертизы.",
    )


# ============================================================
# Агент 8 — санитарно-эпидемиологический контроль (→ Санэпидслужба)
# ============================================================

SANITARY_KEYWORDS = {
    "infection": ["вспышк", "инфекц", "заражени", "эпидеми", "кишечн", "отравлени",
                  "коронавирус", "туберкулёз", "гепатит", "внутрибольничн"],
    "sterility": ["стерильн", "антисанитар", "дезинфекц", "необработанн", "грязн"],
    "waste": ["медицинские отходы", "утилизац", "использованные шприц", "биоотходы"],
    "conditions": ["санитарн", "плесен", "тараканы", "крысы", "грязь в палате"],
}


class SanitaryResult(BaseModel):
    flagged: bool = False
    severity: str = "low"  # low / medium / high / critical
    issue_types: list[str] = Field(default_factory=list)
    route_to: str | None = None
    note: str | None = None


async def sanitary_epid_analyze(appeal: Appeal, db: AsyncSession) -> SanitaryResult:
    await agent_config.get_config(db, "agent8", {})
    t = (appeal.text or "").lower()
    issue_types = [k for k, words in SANITARY_KEYWORDS.items() if any(w in t for w in words)]
    relevant = appeal.category == "sanitary" or bool(issue_types)
    if not relevant or not issue_types:
        return SanitaryResult(flagged=bool(issue_types))
    # Критичность: вспышка инфекции → выше
    if "infection" in issue_types:
        severity = "critical"
    elif {"sterility", "waste"} & set(issue_types):
        severity = "high" if appeal.risk_level in ("high", "critical") else "medium"
    else:
        severity = "low"
    return SanitaryResult(
        flagged=True,
        severity=severity,
        issue_types=issue_types,
        route_to="EPID",
        note="Санитарно-эпидемиологический риск — направить в "
        "санитарно-эпидемиологическую службу для проверки и мер реагирования.",
    )
