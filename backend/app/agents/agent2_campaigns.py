"""Агент 2: выявление массовых и скоординированных кампаний обращений."""
from collections import Counter
from datetime import datetime, timedelta

import numpy as np
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.agents import agent_config, vector_store
from app.agents.llm_client import complete_json
from app.agents.vector_store import SimilarAppeal
from app.models.appeal import Appeal
from app.models.cluster import AppealCluster, ClusterMembership

CAMPAIGN_CONFIG = {
    "similarity_threshold": 0.82,       # порог сходства для включения в кластер
    "min_cluster_size": 5,              # минимум обращений для кластера
    "time_window_hours": 72,            # окно поиска
    "burst_window_minutes": 60,         # окно для «пачки»
    "burst_min_appeals": 8,             # минимум для пачки
    "coordination_score_threshold": 0.65,  # порог для флага кампании
}

CAMPAIGN_LLM_PROMPT = """
Ты — аналитик системы обращений граждан в сфере здравоохранения (MedHubHAQ).

Тебе предоставлен кластер похожих обращений пациентов. Определи: это скоординированная кампания (организованная массовая подача, возможно инициированная в чатах пациентов или соцсетях) или органичная массовая жалоба на реальную проблему медицинской организации/региона?

ПРИЗНАКИ СКООРДИНИРОВАННОЙ КАМПАНИИ:
- Одинаковые или шаблонные формулировки у разных заявителей
- Текст с небольшими вариациями, как по образцу из чата/поста
- Нереально быстрая динамика появления (десятки за час), равномерные интервалы
- Отсутствие конкретных деталей (ФИО врача, отделение, дата приёма)
- Подача из разных регионов, не связанных с темой

ПРИЗНАКИ РЕАЛЬНОЙ МАССОВОЙ ПРОБЛЕМЫ:
- Разные тексты, но одна проблема
- Конкретные детали (больница, отделение, дата, ФИО врача)
- Одна организация/регион
- Постепенный рост, а не пачка

КЛАСТЕР ОБРАЩЕНИЙ (топ-5 для анализа):
{sample_appeals}

СТАТИСТИКА КЛАСТЕРА:
- Всего обращений: {total_count}
- Временной диапазон: {time_range}
- Среднее сходство текстов: {avg_similarity:.2f}
- Разброс по регионам: {regions}
- Пик в час: {peak_per_hour} обращений

Ответь СТРОГО в JSON:
{{
    "is_campaign": true,
    "coordination_score": 0.0,
    "confidence": 0.0,
    "cluster_name": "Краткое название кластера (до 60 символов)",
    "cluster_type": "coordinated_campaign|mass_complaint|group_issue|topic_group",
    "analysis": "Подробный анализ на русском (2-3 предложения)",
    "evidence": ["доказательство 1", "доказательство 2"]
}}
"""


class CampaignResult(BaseModel):
    is_campaign: bool = False
    score: float = 0.0
    cluster_id: int | None = None
    analysis: str = ""
    cluster_name: str | None = None


def calculate_burst_score(similar: list[SimilarAppeal], config: dict) -> float:
    """Максимум обращений в скользящем часовом окне, нормированный к burst_min."""
    if not similar:
        return 0.0
    times = sorted(a.submitted_at for a in similar)
    window = timedelta(minutes=config["burst_window_minutes"])
    peak = 1
    for i, start in enumerate(times):
        count = sum(1 for t in times[i:] if t - start <= window)
        peak = max(peak, count)
    return min(1.0, peak / config["burst_min_appeals"])


def calculate_time_range(similar: list[SimilarAppeal]) -> str:
    times = sorted(a.submitted_at for a in similar)
    span = times[-1] - times[0]
    hours = span.total_seconds() / 3600
    return f"{times[0]:%d.%m %H:%M} — {times[-1]:%d.%m %H:%M} ({hours:.1f} ч)"


def calculate_avg_similarity(similar: list[SimilarAppeal]) -> float:
    if not similar:
        return 0.0
    return float(np.mean([a.similarity for a in similar]))


async def find_or_create_cluster(
    db: AsyncSession, similar: list[SimilarAppeal], appeal: Appeal
) -> AppealCluster:
    # Если похожие обращения уже состоят в кластере — присоединяемся к нему
    similar_ids = [s.id for s in similar]
    existing = (
        await db.execute(
            select(AppealCluster)
            .join(ClusterMembership, ClusterMembership.cluster_id == AppealCluster.id)
            .where(ClusterMembership.appeal_id.in_(similar_ids))
            .limit(1)
        )
    ).scalar_one_or_none()

    if existing is None:
        first_seen = min(a.submitted_at for a in similar + [SimilarAppeal(appeal, 1.0)])
        existing = AppealCluster(
            name=f"Кластер: {appeal.title[:200]}",
            cluster_type="topic_group",
            topic=appeal.title[:200],
            category=appeal.category,
            status="monitoring",
            first_seen=first_seen,
        )
        db.add(existing)
        await db.flush()

    # Добавить недостающие членства
    member_ids = set(
        (
            await db.execute(
                select(ClusterMembership.appeal_id).where(
                    ClusterMembership.cluster_id == existing.id
                )
            )
        ).scalars()
    )
    for s in similar:
        if s.id not in member_ids:
            db.add(
                ClusterMembership(
                    cluster_id=existing.id, appeal_id=s.id, similarity_score=s.similarity
                )
            )
    if appeal.id is not None and appeal.id not in member_ids:
        db.add(
            ClusterMembership(cluster_id=existing.id, appeal_id=appeal.id, similarity_score=1.0)
        )
    await db.flush()

    # Обновить статистику кластера
    member_appeals = [s.appeal for s in similar] + ([appeal] if appeal.id else [])
    existing.appeal_count = len(member_ids | {s.id for s in similar} | ({appeal.id} if appeal.id else set()))
    existing.requester_count = len({a.requester_id for a in member_appeals if a.requester_id})
    existing.region_spread = dict(Counter(a.region for a in member_appeals))
    existing.similarity_score = calculate_avg_similarity(similar)
    existing.last_updated = datetime.utcnow()
    return existing


async def analyze(appeal: Appeal, db: AsyncSession) -> CampaignResult:
    if appeal.embedding is None:
        return CampaignResult()

    config = await agent_config.get_config(db, "agent2", CAMPAIGN_CONFIG)

    # 1. Найти похожие обращения через pgvector
    similar_appeals = await vector_store.find_similar(
        db,
        list(appeal.embedding),
        threshold=config["similarity_threshold"],
        time_window_hours=config["time_window_hours"],
        exclude_id=appeal.id,
    )

    if len(similar_appeals) < config["min_cluster_size"]:
        return CampaignResult()

    # 2. Временные паттерны («пачка»)
    burst_score = calculate_burst_score(similar_appeals, config)

    # 3. Найти или создать кластер
    cluster = await find_or_create_cluster(db, similar_appeals, appeal)
    cluster.peak_rate_per_hour = burst_score * config["burst_min_appeals"]

    # 4. LLM-анализ кластера
    sample_texts = "\n---\n".join(a.text[:300] for a in similar_appeals[:5])
    regions = Counter(a.region for a in similar_appeals)

    prompt = await agent_config.get_prompt(db, "agent2", CAMPAIGN_LLM_PROMPT)
    result = await complete_json(
        prompt.format(
            sample_appeals=sample_texts,
            total_count=len(similar_appeals) + 1,
            time_range=calculate_time_range(similar_appeals),
            avg_similarity=calculate_avg_similarity(similar_appeals),
            regions=dict(regions),
            peak_per_hour=round(burst_score * config["burst_min_appeals"], 1),
        ),
        max_tokens=600,
    )

    cluster.name = result.get("cluster_name") or cluster.name
    cluster.cluster_type = result.get("cluster_type", cluster.cluster_type)
    cluster.description = result.get("analysis", "")
    cluster.coordination_score = float(result.get("coordination_score", 0.0))
    cluster.status = "confirmed_campaign" if result.get("is_campaign") else "monitoring"
    cluster.is_trending = burst_score >= 0.5
    cluster.trend_score = burst_score

    return CampaignResult(
        is_campaign=bool(result.get("is_campaign", False)),
        score=float(result.get("coordination_score", 0.0)),
        cluster_id=cluster.id,
        analysis=result.get("analysis", ""),
        cluster_name=cluster.name,
    )
