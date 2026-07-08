"""Мультитенантность и оргиерархия: арендаторы, регионы, организации, больницы."""
from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.permissions import Role, require_role
from app.database import get_db
from app.models.tenant import HealthcareOrganization, Hospital, Region, Tenant
from app.models.user import User
from app.schemas.tenant import HospitalOut, OrganizationOut, RegionOut, TenantOut

router = APIRouter(prefix="/tenants", tags=["tenants"])


@router.get("", response_model=list[TenantOut])
async def list_tenants(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_role(Role.ANALYST)),
) -> list[Tenant]:
    return list((await db.execute(select(Tenant).order_by(Tenant.id))).scalars())


@router.get("/regions", response_model=list[RegionOut])
async def list_regions(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_role(Role.VIEWER)),
) -> list[Region]:
    return list((await db.execute(select(Region).order_by(Region.name))).scalars())


@router.get("/organizations", response_model=list[OrganizationOut])
async def list_organizations(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_role(Role.VIEWER)),
) -> list[HealthcareOrganization]:
    return list(
        (
            await db.execute(
                select(HealthcareOrganization).order_by(HealthcareOrganization.name)
            )
        ).scalars()
    )


@router.get("/hospitals", response_model=list[HospitalOut])
async def list_hospitals(
    region_id: int | None = None,
    organization_id: int | None = None,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_role(Role.VIEWER)),
) -> list[Hospital]:
    stmt = select(Hospital).order_by(Hospital.name)
    if region_id is not None:
        stmt = stmt.where(Hospital.region_id == region_id)
    if organization_id is not None:
        stmt = stmt.where(Hospital.organization_id == organization_id)
    return list((await db.execute(stmt)).scalars())
