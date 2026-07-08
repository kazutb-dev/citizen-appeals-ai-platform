from datetime import datetime

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.audit import record_audit
from app.core.events import add_appeal_event, notify_requester
from app.core.exceptions import NotFoundError
from app.core.permissions import Role, require_role
from app.database import get_db
from app.models.appeal import Appeal
from app.models.draft import DraftResponse
from app.models.user import User
from app.schemas.draft import DraftOut, DraftUpdate, PaginatedDrafts

router = APIRouter(prefix="/drafts", tags=["drafts"])


def _base_stmt():
    return select(DraftResponse).options(
        selectinload(DraftResponse.appeal).selectinload(Appeal.requester)
    )


async def _get_draft_or_404(db: AsyncSession, draft_id: int) -> DraftResponse:
    draft = (
        await db.execute(_base_stmt().where(DraftResponse.id == draft_id))
    ).scalar_one_or_none()
    if draft is None:
        raise NotFoundError("Проект ответа не найден")
    return draft


@router.get("", response_model=PaginatedDrafts)
async def list_drafts(
    status: str | None = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_role(Role.VIEWER)),
) -> PaginatedDrafts:
    stmt = _base_stmt()
    if status:
        stmt = stmt.where(DraftResponse.status == status)
    total = (
        await db.execute(select(func.count()).select_from(stmt.subquery()))
    ).scalar_one()
    rows = (
        await db.execute(
            stmt.order_by(DraftResponse.created_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
    ).scalars().all()
    return PaginatedDrafts(items=rows, total=total, page=page, page_size=page_size)


@router.get("/{draft_id}", response_model=DraftOut)
async def get_draft(
    draft_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_role(Role.VIEWER)),
) -> DraftResponse:
    return await _get_draft_or_404(db, draft_id)


@router.put("/{draft_id}", response_model=DraftOut)
async def update_draft(
    draft_id: int,
    payload: DraftUpdate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_role(Role.OPERATOR)),
) -> DraftResponse:
    draft = await _get_draft_or_404(db, draft_id)
    draft.draft_text = payload.draft_text
    draft.status = "reviewed"
    draft.reviewed_by_id = user.id
    draft.reviewed_at = datetime.utcnow()
    await record_audit(
        db, action="draft_updated", entity_type="draft", entity_id=draft.id,
        user_id=user.id, actor=user.email,
    )
    await db.commit()
    return await _get_draft_or_404(db, draft_id)


@router.post("/{draft_id}/approve", response_model=DraftOut)
async def approve_draft(
    draft_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_role(Role.ANALYST)),
) -> DraftResponse:
    draft = await _get_draft_or_404(db, draft_id)
    draft.status = "approved"
    draft.reviewed_by_id = user.id
    draft.reviewed_at = datetime.utcnow()
    await add_appeal_event(
        db, draft.appeal_id, "response_approved", actor=user.email,
        comment="Официальный ответ утверждён",
    )
    if draft.appeal is not None:
        await notify_requester(
            db, draft.appeal,
            type="appeal_response",
            title="Получен официальный ответ на ваше обращение",
            body="Ответ доступен в карточке обращения в разделе «Мои обращения».",
        )
    await record_audit(
        db, action="draft_approved", entity_type="draft", entity_id=draft.id,
        user_id=user.id, actor=user.email,
    )
    await db.commit()
    return await _get_draft_or_404(db, draft_id)
