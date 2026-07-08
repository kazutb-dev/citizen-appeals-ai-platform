from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, Query
from sqlalchemy import case, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.permissions import Role, require_role
from app.data.categories import CATEGORY_ROUTING
from app.database import get_db
from app.models.department import Department
from app.models.social import SocialPost
from app.models.user import User
from app.schemas.social import (
    DepartmentImpact,
    PaginatedSocialPosts,
    ReputationPoint,
    SentimentPoint,
    SourceActivity,
    SpikePoint,
    TopicTrend,
    TrendingTopic,
)

router = APIRouter(prefix="/social", tags=["social"])

RISK_ORDER = {"low": 0, "medium": 1, "high": 2, "critical": 3}


@router.get("/posts", response_model=PaginatedSocialPosts)
async def list_posts(
    platform: str | None = None,
    category: str | None = None,
    region: str | None = None,
    risk_level: str | None = None,
    sentiment: str | None = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_role(Role.VIEWER)),
) -> PaginatedSocialPosts:
    stmt = select(SocialPost)
    if platform:
        stmt = stmt.where(SocialPost.platform == platform)
    if category:
        stmt = stmt.where(SocialPost.category == category)
    if region:
        stmt = stmt.where(SocialPost.region == region)
    if risk_level:
        stmt = stmt.where(SocialPost.risk_level == risk_level)
    if sentiment:
        stmt = stmt.where(SocialPost.sentiment == sentiment)

    total = (
        await db.execute(select(func.count()).select_from(stmt.subquery()))
    ).scalar_one()
    rows = (
        await db.execute(
            stmt.order_by(SocialPost.post_date.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
    ).scalars().all()
    return PaginatedSocialPosts(items=rows, total=total, page=page, page_size=page_size)


@router.get("/trending", response_model=list[TrendingTopic])
async def trending(
    limit: int = Query(10, ge=1, le=50),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_role(Role.VIEWER)),
) -> list[TrendingTopic]:
    """Топ упоминаний по темам."""
    rows = (
        await db.execute(
            select(
                SocialPost.topic,
                func.max(SocialPost.category).label("category"),
                func.count(SocialPost.id).label("post_count"),
                func.sum(SocialPost.views).label("total_views"),
                func.array_agg(SocialPost.risk_level).label("risks"),
            )
            .where(SocialPost.topic.is_not(None))
            .group_by(SocialPost.topic)
            .order_by(func.sum(SocialPost.views).desc())
            .limit(limit)
        )
    ).all()
    return [
        TrendingTopic(
            topic=row.topic,
            category=row.category,
            post_count=row.post_count,
            total_views=int(row.total_views or 0),
            max_risk_level=max(row.risks, key=lambda r: RISK_ORDER.get(r, 0)),
        )
        for row in rows
    ]


# ============================================================
# Аналитика
# ============================================================


@router.get("/analytics/sentiment", response_model=list[SentimentPoint])
async def sentiment_timeline(
    days: int = Query(30, ge=1, le=365),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_role(Role.VIEWER)),
) -> list[SentimentPoint]:
    """Динамика тональности постов по дням."""
    since = datetime.utcnow() - timedelta(days=days)
    day = func.date_trunc("day", SocialPost.post_date).label("day")
    rows = (
        await db.execute(
            select(
                day,
                func.sum(case((SocialPost.sentiment == "positive", 1), else_=0)).label("positive"),
                func.sum(case((SocialPost.sentiment == "neutral", 1), else_=0)).label("neutral"),
                func.sum(case((SocialPost.sentiment == "negative", 1), else_=0)).label("negative"),
                func.sum(case((SocialPost.sentiment == "alarming", 1), else_=0)).label("alarming"),
            )
            .where(SocialPost.post_date >= since)
            .group_by(day)
            .order_by(day)
        )
    ).all()
    return [
        SentimentPoint(
            date=row.day.strftime("%Y-%m-%d"),
            positive=int(row.positive or 0),
            neutral=int(row.neutral or 0),
            negative=int(row.negative or 0),
            alarming=int(row.alarming or 0),
        )
        for row in rows
    ]


@router.get("/analytics/trends", response_model=list[TopicTrend])
async def topic_trends(
    window_days: int = Query(7, ge=1, le=90),
    limit: int = Query(10, ge=1, le=50),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_role(Role.VIEWER)),
) -> list[TopicTrend]:
    """Рост/падение тем: текущее окно против предыдущего."""
    now = datetime.utcnow()
    current_start = now - timedelta(days=window_days)
    previous_start = now - timedelta(days=2 * window_days)

    async def topic_counts(start: datetime, end: datetime) -> dict[str, dict]:
        rows = (
            await db.execute(
                select(
                    SocialPost.topic,
                    func.count(SocialPost.id).label("count"),
                    func.sum(case((SocialPost.sentiment.in_(["negative", "alarming"]), 1), else_=0)).label("neg"),
                    func.sum(case((SocialPost.sentiment == "positive", 1), else_=0)).label("pos"),
                )
                .where(
                    SocialPost.topic.is_not(None),
                    SocialPost.post_date >= start,
                    SocialPost.post_date < end,
                )
                .group_by(SocialPost.topic)
            )
        ).all()
        return {
            row.topic: {"count": row.count, "neg": int(row.neg or 0), "pos": int(row.pos or 0)}
            for row in rows
        }

    current = await topic_counts(current_start, now)
    previous = await topic_counts(previous_start, current_start)

    trends: list[TopicTrend] = []
    for topic, stats in current.items():
        prev_count = previous.get(topic, {}).get("count", 0)
        growth = (
            ((stats["count"] - prev_count) / prev_count * 100) if prev_count else 100.0
        )
        if stats["neg"] > stats["pos"]:
            dominant = "negative"
        elif stats["pos"] > stats["neg"]:
            dominant = "positive"
        else:
            dominant = "neutral"
        trends.append(
            TopicTrend(
                topic=topic,
                current_count=stats["count"],
                previous_count=prev_count,
                growth_pct=round(growth, 1),
                dominant_sentiment=dominant,
            )
        )
    trends.sort(key=lambda t: abs(t.growth_pct) * t.current_count, reverse=True)
    return trends[:limit]


@router.get("/analytics/spikes", response_model=list[SpikePoint])
async def spikes(
    days: int = Query(30, ge=7, le=365),
    threshold: float = Query(2.0, ge=1.2, le=10.0),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_role(Role.VIEWER)),
) -> list[SpikePoint]:
    """Дни с аномальным всплеском постов (выше threshold × среднесуточного)."""
    since = datetime.utcnow() - timedelta(days=days)
    day = func.date_trunc("day", SocialPost.post_date).label("day")
    rows = (
        await db.execute(
            select(day, func.count(SocialPost.id).label("count"))
            .where(SocialPost.post_date >= since)
            .group_by(day)
            .order_by(day)
        )
    ).all()
    if not rows:
        return []
    counts = [row.count for row in rows]
    mean = sum(counts) / len(counts)
    if mean <= 0:
        return []
    return [
        SpikePoint(
            date=row.day.strftime("%Y-%m-%d"),
            count=row.count,
            expected=round(mean, 1),
            deviation=round(row.count / mean, 2),
        )
        for row in rows
        if row.count >= mean * threshold
    ]


@router.get("/analytics/sources", response_model=list[SourceActivity])
async def source_activity(
    days: int = Query(30, ge=1, le=365),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_role(Role.VIEWER)),
) -> list[SourceActivity]:
    """Активность по источникам с долей негатива."""
    since = datetime.utcnow() - timedelta(days=days)
    rows = (
        await db.execute(
            select(
                SocialPost.source_name,
                SocialPost.platform,
                func.count(SocialPost.id).label("post_count"),
                func.sum(SocialPost.views).label("total_views"),
                func.sum(case((SocialPost.sentiment.in_(["negative", "alarming"]), 1), else_=0)).label("neg"),
            )
            .where(SocialPost.post_date >= since)
            .group_by(SocialPost.source_name, SocialPost.platform)
            .order_by(func.count(SocialPost.id).desc())
        )
    ).all()
    return [
        SourceActivity(
            source_name=row.source_name,
            platform=row.platform,
            post_count=row.post_count,
            total_views=int(row.total_views or 0),
            negative_share=round(int(row.neg or 0) / row.post_count, 2) if row.post_count else 0.0,
        )
        for row in rows
    ]


@router.get("/analytics/reputation", response_model=list[ReputationPoint])
async def reputation(
    days: int = Query(30, ge=7, le=365),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_role(Role.VIEWER)),
) -> list[ReputationPoint]:
    """Индекс репутации организации по дням: (pos − neg − 2·alarm) / total."""
    since = datetime.utcnow() - timedelta(days=days)
    day = func.date_trunc("day", SocialPost.post_date).label("day")
    rows = (
        await db.execute(
            select(
                day,
                func.count(SocialPost.id).label("total"),
                func.sum(case((SocialPost.sentiment == "positive", 1), else_=0)).label("pos"),
                func.sum(case((SocialPost.sentiment == "negative", 1), else_=0)).label("neg"),
                func.sum(case((SocialPost.sentiment == "alarming", 1), else_=0)).label("alarm"),
            )
            .where(SocialPost.post_date >= since)
            .group_by(day)
            .order_by(day)
        )
    ).all()
    points: list[ReputationPoint] = []
    for row in rows:
        total = row.total or 0
        score = (
            (int(row.pos or 0) - int(row.neg or 0) - 2 * int(row.alarm or 0)) / total
            if total
            else 0.0
        )
        points.append(
            ReputationPoint(
                date=row.day.strftime("%Y-%m-%d"),
                score=round(max(-1.0, min(1.0, score)), 3),
                post_count=total,
            )
        )
    return points


@router.get("/analytics/department-impact", response_model=list[DepartmentImpact])
async def department_impact(
    days: int = Query(30, ge=1, le=365),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_role(Role.VIEWER)),
) -> list[DepartmentImpact]:
    """Какие подразделения затрагивают обсуждения в соцсетях (по категориям постов)."""
    since = datetime.utcnow() - timedelta(days=days)
    rows = (
        await db.execute(
            select(
                SocialPost.category,
                func.count(SocialPost.id).label("post_count"),
                func.sum(case((SocialPost.sentiment.in_(["negative", "alarming"]), 1), else_=0)).label("neg"),
                func.sum(SocialPost.views).label("total_views"),
            )
            .where(SocialPost.category.is_not(None), SocialPost.post_date >= since)
            .group_by(SocialPost.category)
            .order_by(func.count(SocialPost.id).desc())
        )
    ).all()

    departments = {
        d.code: d.short_name or d.name
        for d in (await db.execute(select(Department))).scalars()
    }
    return [
        DepartmentImpact(
            category=row.category,
            department=departments.get(CATEGORY_ROUTING.get(row.category, "")),
            post_count=row.post_count,
            negative_count=int(row.neg or 0),
            total_views=int(row.total_views or 0),
        )
        for row in rows
    ]
