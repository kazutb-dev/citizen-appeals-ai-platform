from datetime import datetime, timedelta

from fastapi import APIRouter, Depends
from sqlalchemy import case, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.permissions import Role, require_role
from app.database import get_db
from app.models.appeal import Appeal
from app.models.audit import AuditLog
from app.models.user import User
from app.schemas.analytics import (
    AgentStat,
    CategoryStat,
    OverviewKpi,
    RegionStat,
    TrendPoint,
)

router = APIRouter(prefix="/analytics", tags=["analytics"])

AGENT_NAMES = {
    "agent1": "Эскалация руководству",
    "agent2": "Кампании",
    "agent3": "Дубликаты",
    "agent4": "Проекты ответов",
    "agent5": "Повторные заявители",
}


@router.get("/overview", response_model=OverviewKpi)
async def overview(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_role(Role.VIEWER)),
) -> OverviewKpi:
    now = datetime.utcnow()
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    yesterday_start = today_start - timedelta(days=1)

    total = (await db.execute(select(func.count(Appeal.id)))).scalar_one()
    today = (
        await db.execute(
            select(func.count(Appeal.id)).where(Appeal.submitted_at >= today_start)
        )
    ).scalar_one()
    yesterday = (
        await db.execute(
            select(func.count(Appeal.id)).where(
                Appeal.submitted_at >= yesterday_start,
                Appeal.submitted_at < today_start,
            )
        )
    ).scalar_one()
    trend = ((today - yesterday) / yesterday * 100) if yesterday else 0.0

    critical_open = (
        await db.execute(
            select(func.count(Appeal.id)).where(
                Appeal.risk_level == "critical",
                Appeal.status.notin_(["resolved", "rejected"]),
            )
        )
    ).scalar_one()
    campaigns = (
        await db.execute(select(func.count(Appeal.id)).where(Appeal.is_campaign.is_(True)))
    ).scalar_one()
    analyzed = (
        await db.execute(select(func.count(Appeal.id)).where(Appeal.analyzed_at.is_not(None)))
    ).scalar_one()

    avg_days_row = (
        await db.execute(
            select(
                func.avg(
                    func.extract("epoch", Appeal.resolved_at - Appeal.submitted_at) / 86400
                )
            ).where(Appeal.resolved_at.is_not(None))
        )
    ).scalar_one()

    return OverviewKpi(
        appeals_today=today,
        appeals_today_trend_pct=round(trend, 1),
        critical_open=critical_open,
        campaigns_detected=campaigns,
        ai_processed=analyzed,
        ai_processed_pct=round(analyzed / total * 100, 1) if total else 0.0,
        avg_response_days=round(float(avg_days_row or 0), 1),
        total_appeals=total,
    )


@router.get("/trends", response_model=list[TrendPoint])
async def trends(
    days: int = 30,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_role(Role.VIEWER)),
) -> list[TrendPoint]:
    since = datetime.utcnow() - timedelta(days=days)
    day = func.date_trunc("day", Appeal.submitted_at).label("day")
    rows = (
        await db.execute(
            select(
                day,
                func.count(Appeal.id).label("count"),
                func.sum(case((Appeal.risk_level == "critical", 1), else_=0)).label("critical"),
            )
            .where(Appeal.submitted_at >= since)
            .group_by(day)
            .order_by(day)
        )
    ).all()
    return [
        TrendPoint(date=row.day.strftime("%Y-%m-%d"), count=row.count, critical=int(row.critical or 0))
        for row in rows
    ]


@router.get("/regions", response_model=list[RegionStat])
async def regions(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_role(Role.VIEWER)),
) -> list[RegionStat]:
    rows = (
        await db.execute(
            select(
                Appeal.region,
                func.count(Appeal.id).label("total"),
                func.sum(case((Appeal.risk_level == "critical", 1), else_=0)).label("critical"),
                func.sum(case((Appeal.is_escalated.is_(True), 1), else_=0)).label("escalated"),
                func.sum(case((Appeal.is_campaign.is_(True), 1), else_=0)).label("campaigns"),
            )
            .group_by(Appeal.region)
            .order_by(func.count(Appeal.id).desc())
        )
    ).all()
    return [
        RegionStat(
            region=row.region,
            total=row.total,
            critical=int(row.critical or 0),
            escalated=int(row.escalated or 0),
            campaigns=int(row.campaigns or 0),
        )
        for row in rows
    ]


@router.get("/categories", response_model=list[CategoryStat])
async def categories(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_role(Role.VIEWER)),
) -> list[CategoryStat]:
    rows = (
        await db.execute(
            select(Appeal.category, func.count(Appeal.id).label("count"))
            .group_by(Appeal.category)
            .order_by(func.count(Appeal.id).desc())
        )
    ).all()
    return [CategoryStat(category=row.category, count=row.count) for row in rows]


@router.get("/agents", response_model=list[AgentStat])
async def agents(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_role(Role.VIEWER)),
) -> list[AgentStat]:
    """Статистика по запускам агентов из журнала аудита."""
    runs = (
        await db.execute(
            select(AuditLog.actor, func.count(AuditLog.id).label("processed"))
            .where(AuditLog.action == "agent_run")
            .group_by(AuditLog.actor)
        )
    ).all()
    runs_map = {row.actor.removeprefix("agent:"): row.processed for row in runs}

    flagged_map = {
        "agent1": (
            await db.execute(
                select(func.count(Appeal.id)).where(
                    Appeal.risk_level.in_(["critical", "high"])
                )
            )
        ).scalar_one(),
        "agent2": (
            await db.execute(
                select(func.count(Appeal.id)).where(Appeal.is_campaign.is_(True))
            )
        ).scalar_one(),
        "agent3": (
            await db.execute(
                select(func.count(Appeal.id)).where(Appeal.is_duplicate.is_(True))
            )
        ).scalar_one(),
        "agent4": (
            await db.execute(select(func.count(Appeal.id)).where(Appeal.analyzed_at.is_not(None)))
        ).scalar_one(),
        "agent5": (
            await db.execute(
                select(func.count(Appeal.id)).where(Appeal.from_repeat_complainant.is_(True))
            )
        ).scalar_one(),
    }

    return [
        AgentStat(
            agent=key,
            name=AGENT_NAMES[key],
            processed=runs_map.get(key, 0),
            flagged=int(flagged_map.get(key, 0)),
        )
        for key in AGENT_NAMES
    ]
