from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.permissions import Role, require_role
from app.database import get_db
from app.models.audit import AuditLog
from app.models.user import User
from app.schemas.analytics import PaginatedAudit

router = APIRouter(prefix="/audit", tags=["audit"])


@router.get("", response_model=PaginatedAudit)
async def list_audit(
    action: str | None = None,
    entity_type: str | None = None,
    actor: str | None = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_role(Role.ANALYST)),
) -> PaginatedAudit:
    stmt = select(AuditLog)
    if action:
        stmt = stmt.where(AuditLog.action == action)
    if entity_type:
        stmt = stmt.where(AuditLog.entity_type == entity_type)
    if actor:
        stmt = stmt.where(AuditLog.actor.ilike(f"%{actor}%"))

    total = (
        await db.execute(select(func.count()).select_from(stmt.subquery()))
    ).scalar_one()
    rows = (
        await db.execute(
            stmt.order_by(AuditLog.created_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
    ).scalars().all()
    return PaginatedAudit(items=rows, total=total, page=page, page_size=page_size)
