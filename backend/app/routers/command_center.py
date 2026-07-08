"""AI Command Center — Медицинский ситуационный центр (Phase 2).

Реальные агрегаты из БД (без синтетики) + утренний AI executive brief и AI
root-cause анализ через локальный LLM. Все счётчики считаются по данным
обращений; при недоступности LLM возвращаются агрегаты без AI-текста.
"""
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, Query, Request
from pydantic import BaseModel, Field
from sqlalchemy import case, func, literal, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.agents import executive_brief, root_cause
from app.core.exceptions import NotFoundError
from app.core.i18n import resolve_language
from app.core.permissions import Role, require_role
from app.data.categories import CATEGORY_GROUPS, CATEGORY_SLA_HOURS
from app.database import get_db
from app.models.department import Department
from app.models.appeal import Appeal, AppealEvent
from app.models.audit import AuditLog
from app.models.draft import DraftResponse
from app.models.requester import Requester
from app.models.tenant import HealthcareOrganization, Hospital, Region
from app.models.user import User

router = APIRouter(prefix="/command-center", tags=["command-center"])

_CLOSED = ("resolved", "rejected")


def _category_label(cat: str) -> str:
    grp = CATEGORY_GROUPS.get(cat)
    return grp["label"] if grp else cat


def _sla_hours_case():
    return case(
        *[(Appeal.category == cat, hours) for cat, hours in CATEGORY_SLA_HOURS.items()],
        else_=72,
    )


# --- Схемы ответа ---
class RegionHeat(BaseModel):
    region: str
    total: int
    critical: int
    lat: float | None = None
    lng: float | None = None


class HospitalRank(BaseModel):
    hospital_id: int
    name: str
    total: int
    critical: int


class CategoryCount(BaseModel):
    category: str
    label: str
    count: int


class SituationSnapshot(BaseModel):
    generated_at: datetime
    appeals_today: int
    appeals_24h: int
    appeals_today_trend_pct: float
    critical_open: int
    escalations: int
    sla_violations: int
    campaigns: int
    duplicates: int
    duplicates_24h: int
    in_progress_now: int
    medicine_shortage: int
    emergency_incidents: int
    ai_runs_today: int
    region_heatmap: list[RegionHeat]
    hospital_ranking: list[HospitalRank]
    category_breakdown: list[CategoryCount]


class CriticalQueueItem(BaseModel):
    id: int
    submitted_at: datetime
    region: str
    category: str
    category_label: str
    status: str
    sla_deadline: datetime
    responsible: str
    priority: str
    department_id: int | None = None
    is_escalated: bool = False


class AppealMapPoint(BaseModel):
    id: int
    title: str
    region: str
    hospital_id: int | None = None
    hospital_name: str | None = None
    category: str
    category_label: str
    status: str
    risk_level: str
    submitted_at: datetime
    latitude: float
    longitude: float
    location_name: str | None = None


class HotspotItem(BaseModel):
    name: str
    total: int
    critical: int
    overdue: int
    open_count: int


class HotspotsOut(BaseModel):
    generated_at: datetime
    regions: list[HotspotItem] = Field(default_factory=list)
    organizations: list[HotspotItem] = Field(default_factory=list)


class ActionItem(BaseModel):
    problem: str
    action: str
    assignee: str


class AiActionsOut(BaseModel):
    generated_at: datetime
    ai_available: bool
    source: str
    items: list[ActionItem] = Field(default_factory=list)


def _sla_deadline(appeal: Appeal) -> datetime:
    hours = CATEGORY_SLA_HOURS.get(appeal.category, 72)
    return appeal.submitted_at + timedelta(hours=hours)


def _priority_for_appeal(appeal: Appeal) -> str:
    deadline = _sla_deadline(appeal)
    if appeal.is_escalated or deadline <= datetime.utcnow() or appeal.category == "emergency":
        return "P0"
    return "P1"


def _fallback_action_items(
    stats: dict, hotspots: list[HotspotItem], queue: list[CriticalQueueItem]
) -> list[ActionItem]:
    items: list[ActionItem] = []
    if queue:
        lead = queue[0]
        items.append(
            ActionItem(
                problem=(
                    f"В очереди {len(queue)} критических обращений; ближайший инцидент — #{lead.id} ({lead.category_label}, {lead.region})."
                ),
                action="Немедленно открыть карточку, подтвердить маршрут и перевести инцидент в работу в течение 15 минут.",
                assignee=lead.responsible or "Дежурный оператор",
            )
        )
    if stats.get("sla_violations", 0) > 0:
        hotspot = hotspots[0] if hotspots else None
        items.append(
            ActionItem(
                problem=(
                    f"Есть {stats['sla_violations']} просроченных SLA."
                    + (f" Наибольшая нагрузка: {hotspot.name}." if hotspot else "")
                ),
                action="Провести разбор просрочки, перераспределить очередь и назначить ответственного за закрытие просроченных кейсов сегодня.",
                assignee=hotspot.name if hotspot else "Руководитель смены",
            )
        )
    if stats.get("critical_open", 0) > 0 and len(items) < 3:
        hotspot = hotspots[1] if len(hotspots) > 1 else (hotspots[0] if hotspots else None)
        items.append(
            ActionItem(
                problem="Открытые критические обращения требуют ежедневного контроля до закрытия.",
                action="Назначить короткий оперативный разбор по критическим обращениям и проверить повторные жалобы по тем же маршрутам.",
                assignee=hotspot.name if hotspot else "Аналитик ситуационного центра",
            )
        )
    return items[:3]


class ExecutiveBriefOut(BaseModel):
    generated_at: datetime
    ai_available: bool
    summary: str | None = None
    stats: dict = Field(default_factory=dict)
    top_categories: list[CategoryCount] = Field(default_factory=list)
    top_regions: list[RegionHeat] = Field(default_factory=list)


@router.get("/situation", response_model=SituationSnapshot)
async def situation(
    tenant_id: int | None = Query(None),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_role(Role.VIEWER)),
) -> SituationSnapshot:
    now = datetime.utcnow()
    today = now.replace(hour=0, minute=0, second=0, microsecond=0)
    yesterday = today - timedelta(days=1)
    last_24h = now - timedelta(hours=24)

    base = [Appeal.tenant_id == tenant_id] if tenant_id is not None else []

    async def count(*conds) -> int:
        return (
            await db.execute(select(func.count(Appeal.id)).where(*base, *conds))
        ).scalar_one()

    appeals_today = await count(Appeal.submitted_at >= today)
    appeals_24h = await count(Appeal.submitted_at >= last_24h)
    appeals_yesterday = await count(
        Appeal.submitted_at >= yesterday, Appeal.submitted_at < today
    )
    critical_open = await count(
        Appeal.risk_level == "critical", Appeal.status.notin_(_CLOSED)
    )
    escalations = await count(Appeal.is_escalated.is_(True), Appeal.status.notin_(_CLOSED))
    campaigns = await count(Appeal.is_campaign.is_(True))
    duplicates = await count(Appeal.status == "duplicate")
    duplicates_24h = await count(Appeal.status == "duplicate", Appeal.submitted_at >= last_24h)
    in_progress_now = await count(Appeal.status.in_(("new", "analyzing", "pending_review", "in_progress")))
    medicine_shortage = await count(Appeal.category == "medicines")
    emergency_incidents = await count(Appeal.category == "emergency")

    age_hours = (
        func.extract("epoch", func.now()) - func.extract("epoch", Appeal.submitted_at)
    ) / 3600.0
    sla_violations = (
        await db.execute(
            select(func.count(Appeal.id)).where(
                *base, Appeal.status.notin_(_CLOSED), age_hours > _sla_hours_case()
            )
        )
    ).scalar_one()

    ai_runs_today = (
        await db.execute(
            select(func.count(AuditLog.id)).where(
                AuditLog.action == "agent_run", AuditLog.created_at >= today
            )
        )
    ).scalar_one()

    # Тепловая карта регионов
    region_rows = (
        await db.execute(
            select(
                Appeal.region,
                func.count(Appeal.id),
                func.sum(case((Appeal.risk_level == "critical", 1), else_=0)),
            )
            .where(*base)
            .group_by(Appeal.region)
            .order_by(func.count(Appeal.id).desc())
        )
    ).all()
    region_coords = {r.name: r for r in (await db.execute(select(Region))).scalars()}
    heatmap = [
        RegionHeat(
            region=row[0],
            total=row[1],
            critical=int(row[2] or 0),
            lat=region_coords[row[0]].lat if row[0] in region_coords else None,
            lng=region_coords[row[0]].lng if row[0] in region_coords else None,
        )
        for row in region_rows
    ]

    # Рейтинг больниц по числу обращений
    hosp_rows = (
        await db.execute(
            select(
                Hospital.id,
                Hospital.name,
                func.count(Appeal.id),
                func.sum(case((Appeal.risk_level == "critical", 1), else_=0)),
            )
            .join(Appeal, Appeal.hospital_id == Hospital.id)
            .where(*base)
            .group_by(Hospital.id, Hospital.name)
            .order_by(func.count(Appeal.id).desc())
            .limit(8)
        )
    ).all()
    hospital_ranking = [
        HospitalRank(hospital_id=row[0], name=row[1], total=row[2], critical=int(row[3] or 0))
        for row in hosp_rows
    ]

    cat_rows = (
        await db.execute(
            select(Appeal.category, func.count(Appeal.id))
            .where(*base)
            .group_by(Appeal.category)
            .order_by(func.count(Appeal.id).desc())
        )
    ).all()
    categories = [
        CategoryCount(category=row[0], label=_category_label(row[0]), count=row[1])
        for row in cat_rows
    ]

    trend = (
        (appeals_today - appeals_yesterday) / appeals_yesterday * 100
        if appeals_yesterday
        else 0.0
    )

    return SituationSnapshot(
        generated_at=now,
        appeals_today=appeals_today,
        appeals_24h=appeals_24h,
        appeals_today_trend_pct=round(trend, 1),
        critical_open=critical_open,
        escalations=escalations,
        sla_violations=sla_violations,
        campaigns=campaigns,
        duplicates=duplicates,
        duplicates_24h=duplicates_24h,
        in_progress_now=in_progress_now,
        medicine_shortage=medicine_shortage,
        emergency_incidents=emergency_incidents,
        ai_runs_today=ai_runs_today,
        region_heatmap=heatmap,
        hospital_ranking=hospital_ranking,
        category_breakdown=categories,
    )


@router.get("/critical-queue", response_model=list[CriticalQueueItem])
async def critical_queue(
    tenant_id: int | None = Query(None),
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_role(Role.VIEWER)),
) -> list[CriticalQueueItem]:
    base = [Appeal.tenant_id == tenant_id] if tenant_id is not None else []
    rows = (
        await db.execute(
            select(Appeal, Department.name, Department.short_name)
            .outerjoin(Department, Appeal.department_id == Department.id)
            .where(*base, Appeal.risk_level == "critical", Appeal.status.notin_(_CLOSED))
            .order_by(Appeal.is_escalated.desc(), Appeal.submitted_at.asc())
            .limit(limit)
        )
    ).all()
    items: list[CriticalQueueItem] = []
    for appeal, department_name, department_short_name in rows:
        items.append(
            CriticalQueueItem(
                id=appeal.id,
                submitted_at=appeal.submitted_at,
                region=appeal.region,
                category=appeal.category,
                category_label=_category_label(appeal.category),
                status=appeal.status,
                sla_deadline=_sla_deadline(appeal),
                responsible=department_short_name or department_name or "Не назначено",
                priority=_priority_for_appeal(appeal),
                department_id=appeal.department_id,
                is_escalated=bool(appeal.is_escalated),
            )
        )
    items.sort(key=lambda item: (item.priority != "P0", item.sla_deadline, item.submitted_at))
    return items


@router.get("/appeals-map", response_model=list[AppealMapPoint])
async def appeals_map(
    tenant_id: int | None = Query(None),
    period_hours: int = Query(24, ge=1, le=720),
    region: str | None = Query(None),
    hospital_id: int | None = Query(None, ge=1),
    risk_level: str | None = Query(None),
    status: str | None = Query(None),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_role(Role.VIEWER)),
) -> list[AppealMapPoint]:
    base = [Appeal.tenant_id == tenant_id] if tenant_id is not None else []
    since = datetime.utcnow() - timedelta(hours=period_hours)
    stmt = (
        select(Appeal, Hospital.name)
        .outerjoin(Hospital, Appeal.hospital_id == Hospital.id)
        .where(
            *base,
            Appeal.latitude.is_not(None),
            Appeal.longitude.is_not(None),
            Appeal.submitted_at >= since,
        )
    )
    if region:
        stmt = stmt.where(Appeal.region == region)
    if hospital_id:
        stmt = stmt.where(Appeal.hospital_id == hospital_id)
    if risk_level:
        stmt = stmt.where(Appeal.risk_level == risk_level)
    if status:
        stmt = stmt.where(Appeal.status == status)
    rows = (await db.execute(stmt.order_by(Appeal.submitted_at.desc()).limit(500))).all()
    return [
        AppealMapPoint(
            id=appeal.id,
            title=appeal.title,
            region=appeal.region,
            hospital_id=appeal.hospital_id,
            hospital_name=hospital_name,
            category=appeal.category,
            category_label=_category_label(appeal.category),
            status=appeal.status,
            risk_level=appeal.risk_level,
            submitted_at=appeal.submitted_at,
            latitude=appeal.latitude,
            longitude=appeal.longitude,
            location_name=appeal.location_name,
        )
        for appeal, hospital_name in rows
        if appeal.latitude is not None and appeal.longitude is not None
    ]


@router.get("/hotspots", response_model=HotspotsOut)
async def hotspots(
    tenant_id: int | None = Query(None),
    period_hours: int = Query(24, ge=1, le=720),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_role(Role.VIEWER)),
) -> HotspotsOut:
    base = [Appeal.tenant_id == tenant_id] if tenant_id is not None else []
    since = datetime.utcnow() - timedelta(hours=period_hours)
    age_hours = (
        func.extract("epoch", func.now()) - func.extract("epoch", Appeal.submitted_at)
    ) / 3600.0

    region_rows = (
        await db.execute(
            select(
                Appeal.region,
                func.count(Appeal.id),
                func.sum(case((Appeal.risk_level == "critical", 1), else_=0)),
                func.sum(case((Appeal.status.notin_(_CLOSED), 1), else_=0)),
                func.sum(case((Appeal.status.notin_(_CLOSED), case((age_hours > _sla_hours_case(), 1), else_=0)), else_=0)),
            )
            .where(*base, Appeal.submitted_at >= since)
            .group_by(Appeal.region)
            .order_by(func.sum(case((Appeal.risk_level == "critical", 1), else_=0)).desc(), func.sum(case((Appeal.status.notin_(_CLOSED), case((age_hours > _sla_hours_case(), 1), else_=0)), else_=0)).desc(), func.count(Appeal.id).desc())
            .limit(8)
        )
    ).all()

    org_name = func.coalesce(HealthcareOrganization.name, Hospital.name, literal("Без привязки"))
    org_rows = (
        await db.execute(
            select(
                org_name,
                func.count(Appeal.id),
                func.sum(case((Appeal.risk_level == "critical", 1), else_=0)),
                func.sum(case((Appeal.status.notin_(_CLOSED), 1), else_=0)),
                func.sum(case((Appeal.status.notin_(_CLOSED), case((age_hours > _sla_hours_case(), 1), else_=0)), else_=0)),
            )
            .outerjoin(Hospital, Appeal.hospital_id == Hospital.id)
            .outerjoin(HealthcareOrganization, Hospital.organization_id == HealthcareOrganization.id)
            .where(*base, Appeal.submitted_at >= since)
            .group_by(org_name)
            .order_by(func.sum(case((Appeal.risk_level == "critical", 1), else_=0)).desc(), func.sum(case((Appeal.status.notin_(_CLOSED), case((age_hours > _sla_hours_case(), 1), else_=0)), else_=0)).desc(), func.count(Appeal.id).desc())
            .limit(8)
        )
    ).all()

    return HotspotsOut(
        generated_at=datetime.utcnow(),
        regions=[
            HotspotItem(name=row[0], total=row[1], critical=int(row[2] or 0), open_count=int(row[3] or 0), overdue=int(row[4] or 0))
            for row in region_rows
        ],
        organizations=[
            HotspotItem(name=row[0], total=row[1], critical=int(row[2] or 0), open_count=int(row[3] or 0), overdue=int(row[4] or 0))
            for row in org_rows
        ],
    )


@router.get("/ai-actions", response_model=AiActionsOut)
async def ai_actions(
    request: Request,
    tenant_id: int | None = Query(None),
    period_hours: int = Query(24, ge=1, le=720),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_role(Role.VIEWER)),
) -> AiActionsOut:
    snapshot = await situation(tenant_id=tenant_id, db=db, user=user)
    queue = await critical_queue(tenant_id=tenant_id, limit=8, db=db, user=user)
    hotspot_payload = await hotspots(tenant_id=tenant_id, period_hours=period_hours, db=db, user=user)
    stats = {
        "appeals_24h": snapshot.appeals_24h,
        "critical_open": snapshot.critical_open,
        "sla_violations": snapshot.sla_violations,
        "escalations": snapshot.escalations,
        "in_progress_now": snapshot.in_progress_now,
        "duplicates_24h": snapshot.duplicates_24h,
    }
    region_hotspots = hotspot_payload.regions[:5]
    try:
        ai_items = await executive_brief.generate_action_recommendations(
            stats,
            [item.model_dump() for item in region_hotspots],
            [item.model_dump() for item in queue],
            lang=resolve_language(request),
        )
        if ai_items:
            return AiActionsOut(
                generated_at=datetime.utcnow(),
                ai_available=True,
                source="llm",
                items=[ActionItem(**item) for item in ai_items],
            )
    except Exception:  # noqa: BLE001
        pass
    fallback = _fallback_action_items(stats, region_hotspots, queue)
    return AiActionsOut(
        generated_at=datetime.utcnow(),
        ai_available=False,
        source="rules",
        items=fallback,
    )


@router.get("/executive-brief", response_model=ExecutiveBriefOut)
async def executive_brief_endpoint(
    request: Request,
    tenant_id: int | None = Query(None),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_role(Role.ANALYST)),
) -> ExecutiveBriefOut:
    snapshot = await situation(tenant_id=tenant_id, db=db, user=user)
    stats = {
        "appeals_today": snapshot.appeals_today,
        "appeals_today_trend_pct": snapshot.appeals_today_trend_pct,
        "critical_open": snapshot.critical_open,
        "escalations": snapshot.escalations,
        "sla_violations": snapshot.sla_violations,
        "campaigns": snapshot.campaigns,
        "duplicates": snapshot.duplicates,
        "medicine_shortage": snapshot.medicine_shortage,
        "emergency_incidents": snapshot.emergency_incidents,
    }
    top_categories = snapshot.category_breakdown[:6]
    top_regions = sorted(
        snapshot.region_heatmap, key=lambda r: r.critical, reverse=True
    )[:5]

    summary: str | None = None
    ai_available = True
    try:
        summary = await executive_brief.generate_brief_text(
            stats,
            [c.model_dump() for c in top_categories],
            [r.model_dump() for r in top_regions],
            lang=resolve_language(request),
        )
    except Exception:  # noqa: BLE001 — LLM недоступен: возвращаем агрегаты без текста
        ai_available = False

    return ExecutiveBriefOut(
        generated_at=snapshot.generated_at,
        ai_available=ai_available,
        summary=summary,
        stats=stats,
        top_categories=top_categories,
        top_regions=top_regions,
    )


@router.get("/root-cause", response_model=root_cause.RootCauseReport)
async def root_cause_endpoint(
    category: str = Query(..., description="Код категории обращений"),
    tenant_id: int | None = Query(None),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_role(Role.ANALYST)),
) -> root_cause.RootCauseReport:
    base = [Appeal.tenant_id == tenant_id] if tenant_id is not None else []
    rows = (
        await db.execute(
            select(Appeal.text)
            .where(*base, Appeal.category == category)
            .order_by(Appeal.submitted_at.desc())
            .limit(12)
        )
    ).all()
    samples = [r[0] for r in rows]
    label = _category_label(category)
    try:
        return await root_cause.analyze_root_cause(category, label, samples)
    except Exception:  # noqa: BLE001 — LLM недоступен: честный empty-state
        return root_cause.RootCauseReport(
            category=category,
            category_label=label,
            sample_size=len(samples),
            ai_available=False,
        )


_EVENT_TITLES = {
    "submitted": "Обращение подано",
    "analysis_started": "Запущен AI-анализ",
    "analysis_done": "AI-анализ завершён",
    "status_changed": "Смена статуса",
    "escalated": "Эскалация руководству",
    "response_drafted": "Подготовлен проект ответа",
}


class TimelineEvent(BaseModel):
    timestamp: datetime
    kind: str
    title: str
    appeal_id: int | None = None
    category: str | None = None
    status: str | None = None
    detail: str | None = None


class PatientTimeline(BaseModel):
    requester_id: int
    full_name: str
    total_appeals: int
    events: list[TimelineEvent]


@router.get("/patient-timeline/{requester_id}", response_model=PatientTimeline)
async def patient_timeline(
    requester_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_role(Role.VIEWER)),
) -> PatientTimeline:
    """AI Timeline: хронологический путь пациента по всем обращениям."""
    requester = (
        await db.execute(select(Requester).where(Requester.id == requester_id))
    ).scalar_one_or_none()
    if requester is None:
        raise NotFoundError("Заявитель не найден")

    appeals = list(
        (
            await db.execute(
                select(Appeal)
                .where(Appeal.requester_id == requester_id)
                .order_by(Appeal.submitted_at)
            )
        ).scalars()
    )
    appeal_ids = [a.id for a in appeals]
    events: list[TimelineEvent] = []
    for a in appeals:
        events.append(
            TimelineEvent(
                timestamp=a.submitted_at,
                kind="appeal",
                title=f"Обращение: {a.title}",
                appeal_id=a.id,
                category=a.category,
                status=a.status,
            )
        )
        if a.resolved_at is not None:
            events.append(
                TimelineEvent(
                    timestamp=a.resolved_at,
                    kind="resolved",
                    title="Обращение решено",
                    appeal_id=a.id,
                    category=a.category,
                    status="resolved",
                )
            )

    if appeal_ids:
        ev_rows = list(
            (
                await db.execute(
                    select(AppealEvent)
                    .where(AppealEvent.appeal_id.in_(appeal_ids))
                    .order_by(AppealEvent.created_at)
                )
            ).scalars()
        )
        for e in ev_rows:
            events.append(
                TimelineEvent(
                    timestamp=e.created_at,
                    kind=f"event:{e.event_type}",
                    title=_EVENT_TITLES.get(e.event_type, e.event_type),
                    appeal_id=e.appeal_id,
                    detail=e.comment,
                )
            )
        dr_rows = list(
            (
                await db.execute(
                    select(DraftResponse).where(DraftResponse.appeal_id.in_(appeal_ids))
                )
            ).scalars()
        )
        for d in dr_rows:
            events.append(
                TimelineEvent(
                    timestamp=d.created_at,
                    kind="response",
                    title=f"Проект ответа ({d.status})",
                    appeal_id=d.appeal_id,
                    status=d.status,
                )
            )

    events.sort(key=lambda ev: ev.timestamp)
    return PatientTimeline(
        requester_id=requester_id,
        full_name=requester.full_name,
        total_appeals=len(appeals),
        events=events,
    )
