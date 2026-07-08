"""Агент 5: анализ повторных заявителей.

Анализирует историю обращений: частоту подачи, повторяющиеся темы,
повторные обращения по ранее решённым вопросам, попытки эскалации.

ВАЖНО: категории влияют ТОЛЬКО на внутреннюю маршрутизацию.
Каждый заявитель имеет право на рассмотрение обращения независимо от категории.
"""
from collections import Counter
from datetime import datetime, timedelta

from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.agents import agent_config
from app.models.appeal import Appeal
from app.models.requester import Requester

REPEAT_CONFIG = {
    "min_appeals_for_analysis": 5,
    "analysis_window_days": 180,

    # Веса для итогового скора
    "weights": {
        "frequency": 0.25,           # частота подачи
        "topic_repetition": 0.35,    # повторяемость одной темы
        "answered_ignored": 0.25,    # повторные обращения по решённым вопросам
        "escalation_attempts": 0.15,  # попытки эскалировать
    },
}

# Маркеры эмоционально-кризисного состояния заявителя. При обнаружении —
# приоритетное человеческое участие (escalation to human), НЕ игнорирование
# и НЕ автоматическое закрытие обращения.
CRISIS_MARKERS = [
    "не вижу смысла", "не видит смысла", "устал жить", "устала жить",
    "не хочу жить", "не хочется жить", "нет смысла жить", "нет выхода",
    "сведу счёты", "свести счёты", "покончить с собой", "покончить с жизнью",
    "жить незачем", "лучше бы меня не было", "не вижу выхода",
]


class RepeatResult(BaseModel):
    score: float = 0.0
    category: str = "active_citizen"
    is_repeat_complainant: bool = False
    frequency_score: float = 0.0
    topic_repetition_score: float = 0.0
    topic_diversity: int = 0
    top_topic: str | None = None
    total_appeals_analyzed: int = 0
    # Этический сигнал: требуется приоритетное человеческое участие
    needs_human_priority: bool = False
    recommendation: str | None = None


async def get_requester_appeals(
    db: AsyncSession, requester_id: int, *, days: int
) -> list[Appeal]:
    cutoff = datetime.utcnow() - timedelta(days=days)
    stmt = (
        select(Appeal)
        .where(Appeal.requester_id == requester_id, Appeal.submitted_at >= cutoff)
        .order_by(Appeal.submitted_at)
    )
    return list((await db.execute(stmt)).scalars().all())


async def get_last_answer_date(
    db: AsyncSession, requester_id: int, category: str
) -> datetime | None:
    stmt = (
        select(Appeal.resolved_at)
        .where(
            Appeal.requester_id == requester_id,
            Appeal.category == category,
            Appeal.resolved_at.is_not(None),
        )
        .order_by(Appeal.resolved_at.desc())
        .limit(1)
    )
    return (await db.execute(stmt)).scalar_one_or_none()


async def analyze(requester: Requester | None, db: AsyncSession) -> RepeatResult:
    if requester is None:
        return RepeatResult()

    config = await agent_config.get_config(db, "agent5", REPEAT_CONFIG)

    recent_appeals = await get_requester_appeals(
        db, requester.id, days=config["analysis_window_days"]
    )

    # Этический приоритет: маркеры кризисного состояния проверяем ВСЕГДА,
    # независимо от количества обращений — это сигнал о возможной угрозе жизни.
    crisis_detected = any(
        marker in (a.text or "").lower()
        for a in recent_appeals
        for marker in CRISIS_MARKERS
    )
    if crisis_detected:
        return RepeatResult(
            category="emotional_crisis",
            total_appeals_analyzed=len(recent_appeals),
            needs_human_priority=True,
            recommendation=(
                "Обнаружены маркеры эмоционально-кризисного состояния. "
                "Требуется приоритетное человеческое участие: подключить "
                "психологическую/социальную службу. Обращение НЕ закрывать "
                "автоматически и рассмотреть по существу в первую очередь."
            ),
        )

    if len(recent_appeals) < config["min_appeals_for_analysis"]:
        return RepeatResult(total_appeals_analyzed=len(recent_appeals))

    # Частотный скор: 10 обращений в месяц = 1.0
    avg_per_month = len(recent_appeals) / 6
    frequency_score = min(1.0, avg_per_month / 10)

    # Повторяемость темы
    topics = [a.category for a in recent_appeals]
    most_common_topic, most_common_topic_count = Counter(topics).most_common(1)[0]
    topic_repetition_score = most_common_topic_count / len(recent_appeals)

    # Повторные обращения после полученного ответа (ранее решённые вопросы)
    answered_count = sum(1 for a in recent_appeals if a.status == "resolved")
    repeated_after_answer = 0
    last_answer_cache: dict[str, datetime | None] = {}
    for a in recent_appeals:
        if a.category not in last_answer_cache:
            last_answer_cache[a.category] = await get_last_answer_date(
                db, requester.id, a.category
            )
        last_answer = last_answer_cache[a.category]
        if last_answer is not None and a.submitted_at > last_answer:
            repeated_after_answer += 1
    answered_ignored_score = min(1.0, repeated_after_answer / max(1, answered_count))

    # Попытки эскалации
    escalation_count = sum(1 for a in recent_appeals if a.is_escalated)
    escalation_score = min(1.0, escalation_count / 5)

    # Итоговый скор
    w = config["weights"]
    total_score = (
        frequency_score * w["frequency"]
        + topic_repetition_score * w["topic_repetition"]
        + answered_ignored_score * w["answered_ignored"]
        + escalation_score * w["escalation_attempts"]
    )

    topic_diversity = len(set(topics))

    # Поведенческая категория (правила, не LLM). Влияет ТОЛЬКО на внутреннюю
    # маршрутизацию — каждое обращение рассматривается по существу.
    if total_score >= 0.85:
        # Высокая активность + признаки организованности
        category = "coordinator"
    elif topic_repetition_score >= 0.6 and total_score >= 0.45:
        # Раз за разом один и тот же вопрос (в т.ч. после ответов)
        category = "chronic_complainant"
    elif frequency_score >= 0.4 and escalation_score > 0 and topic_diversity >= 3:
        # Частые обращения по разным темам с попытками эскалации
        category = "digital_activist"
    elif topic_diversity >= 4 and escalation_score == 0 and total_score < 0.45:
        # Много разных тем, спокойный тон, без эскалаций — наблюдатель/эксперт
        category = "expert_observer"
    elif total_score >= 0.25:
        category = "digital_activist"
    else:
        category = "active_citizen"

    return RepeatResult(
        score=round(total_score, 3),
        category=category,
        is_repeat_complainant=category in ("chronic_complainant", "coordinator"),
        frequency_score=round(frequency_score, 3),
        topic_repetition_score=round(topic_repetition_score, 3),
        topic_diversity=topic_diversity,
        top_topic=most_common_topic,
        total_appeals_analyzed=len(recent_appeals),
    )
