import hashlib
import re
import uuid
from datetime import datetime
from pathlib import Path

import aiofiles
from fastapi import APIRouter, Depends, Query, Request, UploadFile
from fastapi.responses import FileResponse
from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.config import settings
from app.core.audit import record_audit
from app.core.events import add_appeal_event, notify_requester
from app.core.exceptions import ConflictError, ForbiddenError, NotFoundError
from app.core.permissions import Role, require_role
from app.data.categories import VALID_CATEGORIES, route_department_code
from app.data.medical_knowledge import MEDICAL_KNOWLEDGE_BASE
from app.database import get_db
from app.models.appeal import Appeal, AppealAttachment
from app.models.audit import AuditLog
from app.models.department import Department
from app.models.requester import Requester
from app.models.user import User
from app.schemas.appeal import (
    AppealCreate,
    AppealDetail,
    AppealStatusUpdate,
    AppealSubmit,
    MyAppealBrief,
    MyAppealDetail,
    PaginatedAppeals,
    PaginatedMyAppeals,
)

router = APIRouter(prefix="/appeals", tags=["appeals"])

VALID_STATUSES = {
    "new", "analyzing", "pending_review", "in_progress",
    "escalated", "resolved", "rejected", "duplicate",
}

STATUS_LABELS = {
    "new": "Подано",
    "analyzing": "AI-анализ",
    "pending_review": "На рассмотрении",
    "in_progress": "В работе",
    "escalated": "Передано руководству",
    "resolved": "Решено",
    "rejected": "Отклонено",
    "duplicate": "Дубликат",
}

ALLOWED_ATTACHMENT_TYPES = {
    "application/pdf",
    "application/msword",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "application/vnd.ms-excel",
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    "image/png",
    "image/jpeg",
    "text/plain",
}


def hash_pii(value: str) -> str:
    return hashlib.sha256(value.strip().lower().encode()).hexdigest()


def compute_intake_hash(
    source_channel: str, external_ref: str | None, title: str, text: str
) -> str:
    """Хэш идемпотентности приёма — защита от точных дублей между каналами.

    Если у системы-источника есть стабильный идентификатор — хэшируем его; иначе
    хэшируем нормализованное содержание обращения.
    """
    basis = external_ref.strip() if external_ref else f"{title}\n{text}"
    return hashlib.sha256(f"{source_channel}:{basis}".strip().lower().encode()).hexdigest()


async def _get_appeal_or_404(db: AsyncSession, appeal_id: int) -> Appeal:
    stmt = (
        select(Appeal)
        .options(
            selectinload(Appeal.requester),
            selectinload(Appeal.draft_response),
            selectinload(Appeal.attachments),
        )
        .where(Appeal.id == appeal_id)
    )
    appeal = (await db.execute(stmt)).scalar_one_or_none()
    if appeal is None:
        raise NotFoundError(f"Обращение #{appeal_id} не найдено")
    return appeal


async def _route_department(db: AsyncSession, category: str, subcategory: str | None) -> int | None:
    code = route_department_code(category, subcategory)
    dep = (
        await db.execute(select(Department).where(Department.code == code))
    ).scalar_one_or_none()
    return dep.id if dep else None


async def _get_or_create_portal_requester(db: AsyncSession, user: User) -> Requester:
    """Профиль заявителя для пользователя портала; создаётся при первой подаче."""
    if user.requester_id is not None:
        requester = (
            await db.execute(select(Requester).where(Requester.id == user.requester_id))
        ).scalar_one_or_none()
        if requester is not None:
            return requester
    identifier_hash = hash_pii(user.email)
    requester = (
        await db.execute(
            select(Requester).where(Requester.identifier_hash == identifier_hash)
        )
    ).scalar_one_or_none()
    if requester is None:
        requester = Requester(
            identifier_hash=identifier_hash,
            email_hash=identifier_hash,
            full_name=user.full_name,
            requester_type="patient",
            first_appeal_date=datetime.utcnow(),
        )
        db.add(requester)
        await db.flush()
    user.requester_id = requester.id
    return requester


# ============================================================
# Портал заявителя: /appeals/my, /appeals/submit
# (объявлены до /{appeal_id}, чтобы пути не конфликтовали)
# ============================================================


@router.post("/submit", response_model=MyAppealDetail, status_code=201)
async def submit_appeal(
    payload: AppealSubmit,
    request: Request,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_role(Role.REQUESTER)),
) -> MyAppealDetail:
    """Подача обращения пользователем портала (житель, организация, эксперт)."""
    if payload.category not in VALID_CATEGORIES:
        raise ConflictError(f"Недопустимая категория: {payload.category}")

    requester = await _get_or_create_portal_requester(db, user)

    appeal = Appeal(
        requester_id=requester.id,
        title=payload.title,
        text=payload.text,
        category=payload.category,
        subcategory=payload.subcategory,
        region=payload.region,
        district=payload.district,
        latitude=payload.latitude,
        longitude=payload.longitude,
        location_name=payload.location_name,
        source_channel="portal",
        intake_hash=compute_intake_hash("portal", None, payload.title, payload.text),
        department_id=await _route_department(db, payload.category, payload.subcategory),
        status="new",
    )
    db.add(appeal)
    requester.total_appeals = (requester.total_appeals or 0) + 1
    requester.last_appeal_date = datetime.utcnow()
    await db.flush()

    await add_appeal_event(
        db, appeal.id, "submitted", actor=user.email,
        comment="Обращение подано через портал",
    )
    await record_audit(
        db, action="appeal_created", entity_type="appeal", entity_id=appeal.id,
        user_id=user.id, actor=user.email, details={"via": "portal"},
    )
    await db.commit()

    # Анализ агентами — строго в фоновом воркере
    await request.app.state.arq.enqueue_job("analyze_appeal", appeal.id)

    return await _my_appeal_detail(db, appeal.id, user)


@router.get("/my", response_model=PaginatedMyAppeals)
async def my_appeals(
    status: str | None = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_role(Role.REQUESTER)),
) -> PaginatedMyAppeals:
    if user.requester_id is None:
        return PaginatedMyAppeals(items=[], total=0, page=page, page_size=page_size)
    stmt = select(Appeal).where(Appeal.requester_id == user.requester_id)
    if status:
        stmt = stmt.where(Appeal.status == status)
    total = (
        await db.execute(select(func.count()).select_from(stmt.subquery()))
    ).scalar_one()
    rows = (
        await db.execute(
            stmt.order_by(Appeal.submitted_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
    ).scalars().all()
    return PaginatedMyAppeals(items=rows, total=total, page=page, page_size=page_size)


async def _my_appeal_detail(db: AsyncSession, appeal_id: int, user: User) -> MyAppealDetail:
    appeal = (
        await db.execute(
            select(Appeal)
            .options(
                selectinload(Appeal.attachments),
                selectinload(Appeal.events),
                selectinload(Appeal.draft_response),
            )
            .where(Appeal.id == appeal_id)
        )
    ).scalar_one_or_none()
    if appeal is None or appeal.requester_id != user.requester_id:
        raise NotFoundError("Обращение не найдено")

    knowledge = MEDICAL_KNOWLEDGE_BASE.get(appeal.category, MEDICAL_KNOWLEDGE_BASE["other"])
    draft = appeal.draft_response
    # Заявитель видит ответ только после утверждения; внутренние AI-оценки скрыты
    official_response = (
        draft.draft_text if draft and draft.status in ("approved", "sent") else None
    )
    return MyAppealDetail(
        id=appeal.id,
        title=appeal.title,
        category=appeal.category,
        subcategory=appeal.subcategory,
        region=appeal.region,
        district=appeal.district,
        status=appeal.status,
        submitted_at=appeal.submitted_at,
        resolved_at=appeal.resolved_at,
        text=appeal.text,
        attachments=appeal.attachments,
        events=[e for e in appeal.events if e.is_public],
        official_response=official_response,
        response_status=draft.status if draft and official_response else None,
        expected_response_time=knowledge.get("response_time"),
        responsible_department=knowledge.get("responsible_body"),
    )


@router.get("/my/{appeal_id}", response_model=MyAppealDetail)
async def my_appeal_detail(
    appeal_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_role(Role.REQUESTER)),
) -> MyAppealDetail:
    return await _my_appeal_detail(db, appeal_id, user)


# ============================================================
# Вложения
# ============================================================


async def _check_attachment_access(db: AsyncSession, appeal: Appeal, user: User) -> None:
    from app.core.permissions import ROLE_HIERARCHY

    is_staff = ROLE_HIERARCHY.get(user.role, -1) >= ROLE_HIERARCHY[Role.VIEWER]
    is_owner = user.requester_id is not None and appeal.requester_id == user.requester_id
    if not (is_staff or is_owner):
        raise ForbiddenError("Нет доступа к этому обращению")


@router.post("/{appeal_id}/attachments", response_model=AppealDetail, status_code=201)
async def upload_attachment(
    appeal_id: int,
    file: UploadFile,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_role(Role.REQUESTER)),
) -> Appeal:
    appeal = await _get_appeal_or_404(db, appeal_id)
    await _check_attachment_access(db, appeal, user)

    if file.content_type not in ALLOWED_ATTACHMENT_TYPES:
        raise ConflictError(f"Недопустимый тип файла: {file.content_type}")

    max_bytes = settings.MAX_UPLOAD_MB * 1024 * 1024
    safe_name = re.sub(r"[^\w.\-]", "_", file.filename or "file")[:200]
    store_dir = Path(settings.UPLOAD_DIR) / "appeals" / str(appeal_id)
    store_dir.mkdir(parents=True, exist_ok=True)
    storage_path = store_dir / f"{uuid.uuid4().hex}_{safe_name}"

    size = 0
    async with aiofiles.open(storage_path, "wb") as out:
        while chunk := await file.read(1024 * 1024):
            size += len(chunk)
            if size > max_bytes:
                await out.close()
                storage_path.unlink(missing_ok=True)
                raise ConflictError(f"Файл больше {settings.MAX_UPLOAD_MB} МБ")
            await out.write(chunk)

    db.add(
        AppealAttachment(
            appeal_id=appeal_id,
            filename=safe_name,
            content_type=file.content_type,
            size_bytes=size,
            storage_path=str(storage_path),
            uploaded_by_id=user.id,
        )
    )
    await record_audit(
        db, action="attachment_uploaded", entity_type="appeal", entity_id=appeal_id,
        user_id=user.id, actor=user.email, details={"filename": safe_name, "size": size},
    )
    await db.commit()
    return await _get_appeal_or_404(db, appeal_id)


@router.get("/{appeal_id}/attachments/{attachment_id}")
async def download_attachment(
    appeal_id: int,
    attachment_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_role(Role.REQUESTER)),
) -> FileResponse:
    appeal = await _get_appeal_or_404(db, appeal_id)
    await _check_attachment_access(db, appeal, user)
    attachment = (
        await db.execute(
            select(AppealAttachment).where(
                AppealAttachment.id == attachment_id,
                AppealAttachment.appeal_id == appeal_id,
            )
        )
    ).scalar_one_or_none()
    if attachment is None:
        raise NotFoundError("Вложение не найдено")
    return FileResponse(
        attachment.storage_path,
        filename=attachment.filename,
        media_type=attachment.content_type or "application/octet-stream",
    )


# ============================================================
# Служебные эндпоинты (сотрудники организации)
# ============================================================


@router.get("", response_model=PaginatedAppeals)
async def list_appeals(
    status: str | None = None,
    region: str | None = None,
    category: str | None = None,
    risk_level: str | None = None,
    is_escalated: bool | None = None,
    is_campaign: bool | None = None,
    search: str | None = None,
    date_from: datetime | None = None,
    date_to: datetime | None = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_role(Role.VIEWER)),
) -> PaginatedAppeals:
    stmt = select(Appeal).options(selectinload(Appeal.requester))
    if status:
        stmt = stmt.where(Appeal.status == status)
    if region:
        stmt = stmt.where(Appeal.region == region)
    if category:
        stmt = stmt.where(Appeal.category == category)
    if risk_level:
        stmt = stmt.where(Appeal.risk_level == risk_level)
    if is_escalated is not None:
        stmt = stmt.where(Appeal.is_escalated == is_escalated)
    if is_campaign is not None:
        stmt = stmt.where(Appeal.is_campaign == is_campaign)
    if search:
        pattern = f"%{search}%"
        stmt = stmt.where(or_(Appeal.title.ilike(pattern), Appeal.text.ilike(pattern)))
    if date_from:
        stmt = stmt.where(Appeal.submitted_at >= date_from)
    if date_to:
        stmt = stmt.where(Appeal.submitted_at <= date_to)

    total = (
        await db.execute(select(func.count()).select_from(stmt.subquery()))
    ).scalar_one()
    rows = (
        await db.execute(
            stmt.order_by(Appeal.submitted_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
    ).scalars().all()

    return PaginatedAppeals(items=rows, total=total, page=page, page_size=page_size)


@router.post("", response_model=AppealDetail, status_code=201)
async def create_appeal(
    payload: AppealCreate,
    request: Request,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_role(Role.OPERATOR)),
) -> Appeal:
    """Создание обращения оператором от имени заявителя."""
    if payload.category not in VALID_CATEGORIES:
        raise ConflictError(f"Недопустимая категория: {payload.category}")

    requester: Requester | None = None
    if payload.requester_id is not None:
        requester = (
            await db.execute(select(Requester).where(Requester.id == payload.requester_id))
        ).scalar_one_or_none()
        if requester is None:
            raise NotFoundError("Заявитель не найден")
    elif payload.requester_identifier and payload.requester_full_name:
        identifier_hash = hash_pii(payload.requester_identifier)
        requester = (
            await db.execute(
                select(Requester).where(Requester.identifier_hash == identifier_hash)
            )
        ).scalar_one_or_none()
        if requester is None:
            requester = Requester(
                identifier_hash=identifier_hash,
                full_name=payload.requester_full_name,
                requester_type=payload.requester_type or "patient",
                affiliation=payload.affiliation,
                region=payload.region,
                first_appeal_date=datetime.utcnow(),
            )
            db.add(requester)
            await db.flush()
    else:
        raise ConflictError(
            "Укажите requester_id либо requester_identifier + requester_full_name"
        )

    source_channel = (payload.source_channel or "operator").strip().lower()
    appeal = Appeal(
        requester_id=requester.id,
        title=payload.title,
        text=payload.text,
        category=payload.category,
        subcategory=payload.subcategory,
        region=payload.region,
        district=payload.district,
        latitude=payload.latitude,
        longitude=payload.longitude,
        location_name=payload.location_name,
        source_channel=source_channel,
        source_external_ref=payload.external_id,
        intake_hash=compute_intake_hash(
            source_channel, payload.external_id, payload.title, payload.text
        ),
        department_id=await _route_department(db, payload.category, payload.subcategory),
        external_id=payload.external_id,
        status="new",
    )
    db.add(appeal)
    requester.total_appeals = (requester.total_appeals or 0) + 1
    requester.last_appeal_date = datetime.utcnow()
    await db.flush()

    await add_appeal_event(
        db, appeal.id, "submitted", actor=user.email,
        comment=f"Обращение зарегистрировано оператором (канал: {source_channel})",
    )
    await record_audit(
        db, action="appeal_created", entity_type="appeal", entity_id=appeal.id,
        user_id=user.id, actor=user.email,
    )
    await db.commit()

    # Анализ агентами — строго в фоновом воркере
    await request.app.state.arq.enqueue_job("analyze_appeal", appeal.id)

    return await _get_appeal_or_404(db, appeal.id)


@router.get("/{appeal_id}", response_model=AppealDetail)
async def get_appeal(
    appeal_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_role(Role.VIEWER)),
) -> Appeal:
    return await _get_appeal_or_404(db, appeal_id)


@router.put("/{appeal_id}/status", response_model=AppealDetail)
async def update_status(
    appeal_id: int,
    payload: AppealStatusUpdate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_role(Role.OPERATOR)),
) -> Appeal:
    if payload.status not in VALID_STATUSES:
        raise ConflictError(f"Недопустимый статус: {payload.status}")
    appeal = await _get_appeal_or_404(db, appeal_id)
    old_status = appeal.status
    appeal.status = payload.status
    if payload.status == "resolved":
        appeal.resolved_at = datetime.utcnow()
        if appeal.requester:
            appeal.requester.resolved_appeals = (appeal.requester.resolved_appeals or 0) + 1
    if payload.status == "rejected" and appeal.requester:
        appeal.requester.rejected_appeals = (appeal.requester.rejected_appeals or 0) + 1

    await add_appeal_event(
        db, appeal_id, "status_changed", actor=user.email,
        comment=payload.comment,
        details={"from": old_status, "to": payload.status},
    )
    await notify_requester(
        db, appeal,
        type="appeal_status",
        title=f"Статус обращения изменён: {STATUS_LABELS.get(payload.status, payload.status)}",
        body=payload.comment,
    )
    await record_audit(
        db, action="appeal_status_changed", entity_type="appeal", entity_id=appeal.id,
        user_id=user.id, actor=user.email,
        details={"from": old_status, "to": payload.status, "comment": payload.comment},
    )
    await db.commit()
    return await _get_appeal_or_404(db, appeal_id)


@router.post("/{appeal_id}/analyze", response_model=dict)
async def reanalyze(
    appeal_id: int,
    request: Request,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_role(Role.ANALYST)),
) -> dict:
    await _get_appeal_or_404(db, appeal_id)
    await record_audit(
        db, action="appeal_reanalyze", entity_type="appeal", entity_id=appeal_id,
        user_id=user.id, actor=user.email,
    )
    await db.commit()
    await request.app.state.arq.enqueue_job("analyze_appeal", appeal_id)
    return {"detail": "Анализ поставлен в очередь", "appeal_id": appeal_id}


@router.get("/{appeal_id}/analysis")
async def appeal_analysis(
    appeal_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_role(Role.VIEWER)),
) -> dict:
    """Результаты всех агентов (1–8) по обращению, взятые из журнала аудита.

    Возвращает последний запуск каждого агента для данного обращения.
    Используется панелью AppealDetail для отображения полного анализа.
    """
    rows = (
        await db.execute(
            select(AuditLog.actor, AuditLog.details, AuditLog.created_at)
            .where(
                AuditLog.action == "agent_run",
                AuditLog.entity_type == "appeal",
                AuditLog.entity_id == appeal_id,
            )
            .order_by(AuditLog.created_at.desc())
        )
    ).all()
    # Берём последний запуск для каждого агента.
    results: dict = {}
    for actor, details, _ in rows:
        agent = (actor or "").removeprefix("agent:")
        if agent and agent not in results:
            results[agent] = details or {}
    return results


@router.post("/{appeal_id}/escalate", response_model=AppealDetail)
async def escalate(
    appeal_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_role(Role.ANALYST)),
) -> Appeal:
    appeal = await _get_appeal_or_404(db, appeal_id)
    appeal.is_escalated = True
    appeal.escalation_level = appeal.escalation_level or "dean"
    appeal.escalation_reason = appeal.escalation_reason or "Ручная эскалация"
    appeal.escalated_at = datetime.utcnow()
    appeal.status = "escalated"
    await add_appeal_event(
        db, appeal_id, "escalated", actor=user.email,
        details={"manual": True}, is_public=False,
    )
    await record_audit(
        db, action="appeal_escalated", entity_type="appeal", entity_id=appeal.id,
        user_id=user.id, actor=user.email, details={"manual": True},
    )
    await db.commit()
    return await _get_appeal_or_404(db, appeal_id)
