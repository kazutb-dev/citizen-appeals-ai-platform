from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.exceptions import NotFoundError
from app.core.permissions import Role, require_role
from app.database import get_db
from app.models.appeal import Appeal
from app.models.cluster import AppealCluster, ClusterMembership
from app.models.user import User
from app.schemas.appeal import AppealBrief
from app.schemas.cluster import ClusterOut

router = APIRouter(prefix="/clusters", tags=["clusters"])


@router.get("", response_model=list[ClusterOut])
async def list_clusters(
    status: str | None = None,
    cluster_type: str | None = None,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_role(Role.VIEWER)),
) -> list[AppealCluster]:
    stmt = select(AppealCluster).order_by(AppealCluster.coordination_score.desc())
    if status:
        stmt = stmt.where(AppealCluster.status == status)
    if cluster_type:
        stmt = stmt.where(AppealCluster.cluster_type == cluster_type)
    return list((await db.execute(stmt)).scalars().all())


@router.get("/{cluster_id}", response_model=ClusterOut)
async def get_cluster(
    cluster_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_role(Role.VIEWER)),
) -> AppealCluster:
    cluster = (
        await db.execute(select(AppealCluster).where(AppealCluster.id == cluster_id))
    ).scalar_one_or_none()
    if cluster is None:
        raise NotFoundError("Кластер не найден")
    return cluster


@router.get("/{cluster_id}/appeals", response_model=list[AppealBrief])
async def cluster_appeals(
    cluster_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_role(Role.VIEWER)),
) -> list[Appeal]:
    rows = (
        await db.execute(
            select(Appeal)
            .options(selectinload(Appeal.requester))
            .join(ClusterMembership, ClusterMembership.appeal_id == Appeal.id)
            .where(ClusterMembership.cluster_id == cluster_id)
            .order_by(Appeal.submitted_at.desc())
        )
    ).scalars().all()
    return list(rows)
