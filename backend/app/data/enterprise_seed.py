"""Enterprise seed (Phase 2): арендатор по умолчанию, регионы, организации,
больницы и backfill tenant_id/hospital_id для существующих данных.

Запуск (после `alembic upgrade head` и основного seed):

    python -m app.data.enterprise_seed

Идемпотентно: повторный запуск не создаёт дубликатов.
"""
import asyncio

from sqlalchemy import func, select, update

from app.data.regions_data import KZ_REGIONS_GEO
from app.database import async_session_factory
from app.models import (
    Appeal,
    Department,
    HealthcareOrganization,
    Hospital,
    Region,
    Requester,
    Tenant,
    User,
)

DEFAULT_TENANT = {
    "name": "Управление общественного здравоохранения (демо)",
    "slug": "default",
    "plan": "enterprise",
    "is_active": True,
    "contact_email": "info@medhubhaq.kz",
    "branding": {
        "product_name": "MedHubHAQ",
        "subtitle": "AI Citizen Healthcare Appeals Intelligence Platform",
        "primary_color": "#00B0AD",
    },
    "ai_config": {
        "llm_provider": "ollama",
        "llm_model": "qwen2.5:7b-instruct",
        "embedding_model": "BAAI/bge-m3",
        "reranker_model": "BAAI/bge-reranker-v2-m3",
        "temperature": 0.2,
    },
    "settings": {"locale": "ru", "channels": ["portal", "ikomek", "crm", "eotinish"]},
}


async def ensure_tenant(db) -> Tenant:
    tenant = (
        await db.execute(select(Tenant).where(Tenant.slug == DEFAULT_TENANT["slug"]))
    ).scalar_one_or_none()
    if tenant is None:
        tenant = Tenant(**DEFAULT_TENANT)
        db.add(tenant)
        await db.flush()
    return tenant


async def ensure_regions(db) -> dict[str, Region]:
    by_name: dict[str, Region] = {
        r.name: r for r in (await db.execute(select(Region))).scalars()
    }
    for geo in KZ_REGIONS_GEO:
        if geo["name"] not in by_name:
            region = Region(**geo)
            db.add(region)
            by_name[geo["name"]] = region
    await db.flush()
    return by_name


async def ensure_org_and_hospitals(
    db, tenant: Tenant, regions: dict[str, Region]
) -> dict[str, list[Hospital]]:
    """Создаёт по одной организации и двум больницам на регион. Возвращает
    отображение имя_региона -> [больницы] для backfill обращений."""
    existing_orgs = {
        o.code: o for o in (await db.execute(select(HealthcareOrganization))).scalars()
    }
    existing_hosp = {
        h.code: h for h in (await db.execute(select(Hospital))).scalars()
    }
    hospitals_by_region: dict[str, list[Hospital]] = {}

    for geo in KZ_REGIONS_GEO:
        region = regions[geo["name"]]
        org_code = f"UOZ-{geo['code']}"
        org = existing_orgs.get(org_code)
        if org is None:
            org = HealthcareOrganization(
                tenant_id=tenant.id,
                region_id=region.id,
                name=f"Управление общественного здравоохранения — {geo['name']}",
                code=org_code,
                org_type="health_department",
                is_active=True,
            )
            db.add(org)
            await db.flush()
            existing_orgs[org_code] = org

        region_hospitals: list[Hospital] = []
        specs = [
            (f"H-{geo['code']}-1", f"Областная многопрофильная больница — {geo['center']}",
             "multidisciplinary", 420),
            (f"H-{geo['code']}-2", f"Городская поликлиника №1 — {geo['center']}",
             "polyclinic", 0),
        ]
        for code, name, htype, beds in specs:
            hosp = existing_hosp.get(code)
            if hosp is None:
                hosp = Hospital(
                    tenant_id=tenant.id,
                    organization_id=org.id,
                    region_id=region.id,
                    name=name,
                    code=code,
                    hospital_type=htype,
                    beds=beds,
                    address=f"{geo['center']}, Республика Казахстан",
                    is_active=True,
                )
                db.add(hosp)
                await db.flush()
                existing_hosp[code] = hosp
            region_hospitals.append(hosp)
        hospitals_by_region[geo["name"]] = region_hospitals

    return hospitals_by_region


async def backfill_tenant(db, tenant: Tenant) -> None:
    for model in (Appeal, Department, User, Requester):
        await db.execute(
            update(model).where(model.tenant_id.is_(None)).values(tenant_id=tenant.id)
        )


async def backfill_hospitals(db, hospitals_by_region: dict[str, list[Hospital]]) -> int:
    """Привязывает существующие обращения к больнице их региона (round-robin
    между двумя больницами региона для разнообразия рейтинга)."""
    appeals = list(
        (await db.execute(select(Appeal).where(Appeal.hospital_id.is_(None)))).scalars()
    )
    assigned = 0
    for appeal in appeals:
        hospitals = hospitals_by_region.get(appeal.region)
        if not hospitals:
            continue
        appeal.hospital_id = hospitals[appeal.id % len(hospitals)].id
        assigned += 1
    await db.flush()
    return assigned


async def seed_enterprise() -> None:
    async with async_session_factory() as db:
        tenant = await ensure_tenant(db)
        regions = await ensure_regions(db)
        hospitals_by_region = await ensure_org_and_hospitals(db, tenant, regions)
        await backfill_tenant(db, tenant)
        assigned = await backfill_hospitals(db, hospitals_by_region)
        await db.commit()

        org_count = (
            await db.execute(select(func.count(HealthcareOrganization.id)))
        ).scalar_one()
        hosp_count = (await db.execute(select(func.count(Hospital.id)))).scalar_one()
        region_count = (await db.execute(select(func.count(Region.id)))).scalar_one()
        print(
            f"Enterprise seed готов: tenant='{tenant.slug}', регионов={region_count}, "
            f"организаций={org_count}, больниц={hosp_count}, "
            f"обращений привязано к больницам={assigned}."
        )


if __name__ == "__main__":
    asyncio.run(seed_enterprise())
