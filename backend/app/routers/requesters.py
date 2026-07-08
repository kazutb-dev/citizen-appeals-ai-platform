from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.exceptions import NotFoundError
from app.core.permissions import Role, require_role
from app.database import get_db
from app.models.appeal import Appeal
from app.models.requester import Requester
from app.models.user import User
from app.schemas.appeal import AppealBrief
from app.schemas.requester import PaginatedRequesters, RequesterOut

router = APIRouter(prefix="/requesters", tags=["requesters"])


@router.get("", response_model=PaginatedRequesters)
async def list_requesters(
    category: str | None = None,
    requester_type: str | None = None,
    region: str | None = None,
    search: str | None = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_role(Role.VIEWER)),
) -> PaginatedRequesters:
    stmt = select(Requester)
    if category:
        stmt = stmt.where(Requester.category == category)
    if requester_type:
        stmt = stmt.where(Requester.requester_type == requester_type)
    if region:
        stmt = stmt.where(Requester.region == region)
    if search:
        stmt = stmt.where(Requester.full_name.ilike(f"%{search}%"))

    total = (
        await db.execute(select(func.count()).select_from(stmt.subquery()))
    ).scalar_one()
    rows = (
        await db.execute(
            stmt.order_by(Requester.total_appeals.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
    ).scalars().all()
    return PaginatedRequesters(items=rows, total=total, page=page, page_size=page_size)


@router.get("/{requester_id}", response_model=RequesterOut)
async def get_requester(
    requester_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_role(Role.VIEWER)),
) -> Requester:
    requester = (
        await db.execute(select(Requester).where(Requester.id == requester_id))
    ).scalar_one_or_none()
    if requester is None:
        raise NotFoundError("Заявитель не найден")
    return requester


@router.get("/{requester_id}/appeals", response_model=list[AppealBrief])
async def requester_appeals(
    requester_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_role(Role.VIEWER)),
) -> list[Appeal]:
    rows = (
        await db.execute(
            select(Appeal)
            .options(selectinload(Appeal.requester))
            .where(Appeal.requester_id == requester_id)
            .order_by(Appeal.submitted_at.desc())
        )
    ).scalars().all()
    return list(rows)
