"""Загрузка синтетических демо-данных MedHubHAQ (здравоохранение). Запуск:

    python -m app.data.seed [--force]

Создаёт: подразделения медорганизации, тестовых пользователей (пароли — из env),
~260 обращений по 6 сценариям с embeddings (pgvector), кластеры,
проекты ответов, 50 постов соцсетей, настройки агентов, демо-источники
соцсетей и записи журнала аудита.

--force очищает существующие данные обращений перед загрузкой.
"""
import asyncio
import hashlib
import random
import sys
from collections import Counter
from datetime import timedelta

from sqlalchemy import func, select, text

from app.agents.agent_config import ensure_defaults
from app.agents.embedding_service import encode_batch
from app.config import settings
from app.core.auth import hash_password
from app.data.departments_data import DEPARTMENTS
from app.data.regions_data import coords_for_region
from app.data.synthetic_appeals import build_all_appeals
from app.data.synthetic_social import build_social_posts
from app.data.medical_knowledge import MEDICAL_KNOWLEDGE_BASE
from app.database import async_session_factory
from app.models import (
    Appeal,
    AppealCluster,
    AppealEvent,
    AuditLog,
    ClusterMembership,
    Department,
    DraftResponse,
    Requester,
    SocialPost,
    SocialSource,
    User,
)

SEED_USERS = [
    {
        "email": "admin@medhubhaq.kz",
        "full_name": "Администратор платформы",
        "role": "admin",
        "env_key": "SEED_ADMIN_PASSWORD",
    },
    {
        "email": "analyst@medhubhaq.kz",
        "full_name": "Аналитик платформы",
        "role": "analyst",
        "env_key": "SEED_ANALYST_PASSWORD",
    },
    {
        "email": "operator@medhubhaq.kz",
        "full_name": "Оператор обращений",
        "role": "operator",
        "env_key": "SEED_OPERATOR_PASSWORD",
    },
    {
        "email": "patient@medhubhaq.kz",
        "full_name": "Тестовый пациент",
        "role": "requester",
        "env_key": "SEED_PATIENT_PASSWORD",
        "requester_type": "patient",
        "affiliation": "Астана",
    },
    {
        "email": "doctor@medhubhaq.kz",
        "full_name": "Тестовый врач",
        "role": "requester",
        "env_key": "SEED_DOCTOR_PASSWORD",
        "requester_type": "medical_worker",
        "affiliation": "Поликлиника",
    },
    {
        "email": "nurse@medhubhaq.kz",
        "full_name": "Тестовая медсестра",
        "role": "requester",
        "env_key": "SEED_NURSE_PASSWORD",
        "requester_type": "medical_worker",
        "affiliation": "Стационар",
    },
]

CLUSTER_SCENARIOS = {
    "campaign_medicines": {
        "name": "Координированная кампания: отсутствие льготных лекарств",
        "description": "Скоординированная кампания однотипных обращений об "
        "отсутствии льготных лекарств: шаблонные тексты, пачки обращений в час, "
        "подача из разных регионов без конкретных деталей.",
        "cluster_type": "coordinated_campaign",
        "topic": "Отсутствие льготных лекарств",
        "category": "medicines",
        "coordination_score": 0.82,
        "similarity_score": 0.88,
        "peak_rate_per_hour": 18.0,
        "growth_rate": 240.0,
        "is_trending": True,
        "trend_score": 0.9,
        "status": "confirmed_campaign",
    },
    "outbreak_resonance": {
        "name": "Вспышка инфекции в стационаре (социальный резонанс)",
        "description": "Органичная массовая проблема: разные тексты с конкретными "
        "деталями о вспышке кишечной инфекции в стационаре, всплеск за ~72 часа, "
        "синхронный с ростом упоминаний в социальных сетях.",
        "cluster_type": "mass_complaint",
        "topic": "Вспышка инфекции в стационаре",
        "category": "sanitary",
        "coordination_score": 0.24,
        "similarity_score": 0.73,
        "peak_rate_per_hour": 4.0,
        "growth_rate": 120.0,
        "is_trending": True,
        "trend_score": 0.82,
        "status": "active",
    },
    "duplicates": {
        "name": "Повторные обращения (дубликаты)",
        "description": "Дубликаты: заявители повторно подают тот же вопрос. "
        "Высокое попарное сходство текстов внутри одного заявителя, без признаков "
        "организованной кампании.",
        "cluster_type": "duplicate",
        "topic": "Повторная подача обращений",
        "category": "other",
        "coordination_score": 0.1,
        "similarity_score": 0.9,
        "peak_rate_per_hour": 0.5,
        "growth_rate": 5.0,
        "is_trending": False,
        "trend_score": 0.2,
        "status": "monitoring",
    },
}

DEMO_SOURCES = [
    {
        "name": "Региональный новостной Instagram",
        "platform": "instagram",
        "url": "https://www.instagram.com/region_news_demo",
        "polling_interval_minutes": 60,
        "is_enabled": False,  # включается после настройки Instagram Graph API
        "last_status": "not_configured",
    },
    {
        "name": "Городской Telegram-канал жалоб",
        "platform": "telegram",
        "url": "https://t.me/city_appeals_demo",
        "polling_interval_minutes": 30,
        "is_enabled": False,
        "last_status": "pending",
    },
]


def synthetic_identifier_hash(requester_key: str) -> str:
    # Синтетический идентификатор — детерминированный, реальные ID не используются
    return hashlib.sha256(f"SYNTH-NCAIP-{requester_key}".encode()).hexdigest()


def build_draft_text(appeal_data: dict) -> str:
    knowledge = MEDICAL_KNOWLEDGE_BASE.get(
        appeal_data["category"], MEDICAL_KNOWLEDGE_BASE["other"]
    )
    regulations = "\n".join(f"— {r}" for r in knowledge["regulations"])
    actions = knowledge.get("typical_actions") or [
        "Обращение направлено в ответственное подразделение для рассмотрения по существу",
    ]
    actions_text = "\n".join(f"{i + 1}. {a}" for i, a in enumerate(actions))
    return (
        f"Уважаемый(ая) {appeal_data['requester_name'].split()[1]}!\n\n"
        f"Ваше обращение по вопросу «{appeal_data['title']}» рассмотрено. "
        "Сообщаем, что в соответствии с применимыми нормативными документами "
        "(синтетический справочный корпус):\n"
        f"{regulations}\n\n"
        "По Вашему обращению будут предприняты следующие шаги:\n"
        f"{actions_text}\n\n"
        f"Срок рассмотрения: {knowledge['response_time']}. "
        f"Ответственное подразделение: {knowledge['responsible_body']}.\n\n"
        "О результатах рассмотрения Вы будете уведомлены через портал обращений.\n\n"
        "С уважением,\nMedHubHAQ — система обращений (синтетический ответ)"
    )


async def seed() -> None:
    force = "--force" in sys.argv

    async with async_session_factory() as db:
        existing = (await db.execute(select(func.count(Appeal.id)))).scalar_one()
        if existing and not force:
            print(
                f"В базе уже {existing} обращений. Запустите с --force для перезагрузки.",
                file=sys.stderr,
            )
            sys.exit(1)
        if existing and force:
            print("Очистка существующих данных…")
            for table in (
                "cluster_memberships", "draft_responses", "social_posts",
                "appeal_events", "appeal_attachments", "notifications",
                "audit_logs", "appeals", "appeal_clusters", "requesters",
            ):
                await db.execute(text(f"TRUNCATE TABLE {table} RESTART IDENTITY CASCADE"))
            await db.commit()

        # --- Профильные ведомства ---
        department_by_code: dict[str, int] = {}
        department_by_category: dict[str, int] = {}
        for d in DEPARTMENTS:
            existing_d = (
                await db.execute(select(Department).where(Department.name == d["name"]))
            ).scalar_one_or_none()
            if existing_d is None:
                existing_d = Department(**d)
                db.add(existing_d)
                await db.flush()
            department_by_code[d["code"]] = existing_d.id
            for cat in d["categories"]:
                department_by_category.setdefault(cat, existing_d.id)

        # --- Настройки агентов ---
        await ensure_defaults(db)

        # --- Тестовые пользователи (пароли только из env) ---
        for demo_user in SEED_USERS:
            email = demo_user["email"]
            full_name = demo_user["full_name"]
            role = demo_user["role"]
            env_key = demo_user["env_key"]
            password = getattr(settings, env_key)
            if not password:
                print(f"Не задан {env_key} — пользователь {email} пропущен", file=sys.stderr)
                continue
            if len(password) < 8:
                print(
                    f"{env_key}: пароль короче 8 символов — пользователь {email} пропущен",
                    file=sys.stderr,
                )
                continue

            requester_id = None
            position = None
            if role == "requester":
                requester_type = demo_user.get("requester_type", "patient")
                affiliation = demo_user.get("affiliation")
                identifier_hash = hashlib.sha256(email.strip().lower().encode()).hexdigest()
                requester = (
                    await db.execute(
                        select(Requester).where(Requester.identifier_hash == identifier_hash)
                    )
                ).scalar_one_or_none()
                if requester is None:
                    requester = Requester(
                        identifier_hash=identifier_hash,
                        email_hash=identifier_hash,
                        full_name=full_name,
                        requester_type=requester_type,
                        affiliation=affiliation,
                    )
                    db.add(requester)
                    await db.flush()
                else:
                    requester.full_name = full_name
                    requester.requester_type = requester_type
                    requester.affiliation = affiliation
                    requester.email_hash = identifier_hash
                requester_id = requester.id

                from app.data.categories import REQUESTER_TYPES
                position = REQUESTER_TYPES.get(requester_type)

            existing_u = (
                await db.execute(select(User).where(User.email == email))
            ).scalar_one_or_none()
            if existing_u is None:
                db.add(
                    User(
                        email=email,
                        full_name=full_name,
                        role=role,
                        hashed_password=hash_password(password),
                        requester_id=requester_id,
                        position=position,
                        is_active=True,
                    )
                )
            else:
                existing_u.full_name = full_name
                existing_u.role = role
                existing_u.hashed_password = hash_password(password)
                existing_u.requester_id = requester_id
                existing_u.position = position
                existing_u.is_active = True
        await db.flush()

        # --- Демо-источники соцсетей (выключены до настройки ключей) ---
        for src in DEMO_SOURCES:
            existing_s = (
                await db.execute(select(SocialSource).where(SocialSource.name == src["name"]))
            ).scalar_one_or_none()
            if existing_s is None:
                db.add(SocialSource(**src))
        await db.flush()

        # --- Обращения и заявители ---
        appeal_data = build_all_appeals()
        print(f"Генерация embeddings для {len(appeal_data)} обращений "
              f"({settings.EMBEDDING_MODEL})…")
        embeddings = await encode_batch([a["text"] for a in appeal_data], prefix="query")

        requesters: dict[str, Requester] = {}
        appeals: list[Appeal] = []
        # Детерминированный РНГ для гео-разброса и каналов (воспроизводимость seed).
        geo_rng = random.Random(20260611)
        # Распределение обращений по каналам-источникам (единый учёт).
        intake_channels = (
            ["portal"] * 40 + ["eotinish"] * 20 + ["ikomek"] * 15
            + ["crm"] * 12 + ["damumed"] * 8 + ["telegram"] * 3 + ["instagram"] * 2
        )
        for data, embedding in zip(appeal_data, embeddings):
            key = data["requester_key"]
            if key not in requesters:
                requester = Requester(
                    identifier_hash=synthetic_identifier_hash(key),
                    full_name=data["requester_name"],
                    requester_type=data.get("requester_type", "patient"),
                    affiliation=data.get("affiliation"),
                    region=data["region"],
                )
                db.add(requester)
                requesters[key] = requester
            await db.flush()

            # Единый учёт: канал-источник и координаты места (карта обращений).
            _channel = geo_rng.choice(intake_channels)
            _lat, _lng = coords_for_region(data["region"], jitter=0.12, rng=geo_rng)

            appeal = Appeal(
                requester_id=requesters[key].id,
                department_id=department_by_category.get(data["category"]),
                external_id=f"NCAIP-{2026}-{100000 + len(appeals)}",
                title=data["title"],
                text=data["text"],
                category=data["category"],
                subcategory=data.get("subcategory"),
                region=data["region"],
                district=data.get("district"),
                latitude=_lat,
                longitude=_lng,
                location_name=data["region"],
                source_channel=_channel,
                source_external_ref=None,
                intake_hash=hashlib.sha256(
                    f"{_channel}:{data['title']}\n{data['text']}".lower().encode()
                ).hexdigest(),
                status=data["status"],
                risk_level=data["risk_level"],
                risk_score=data["risk_score"],
                risk_reasons=data["risk_reasons"],
                tags=data["tags"],
                is_escalated=data.get("is_escalated", False),
                escalation_level=data.get("escalation_level"),
                escalation_reason=data.get("escalation_reason"),
                escalated_at=data["submitted_at"] + timedelta(minutes=4)
                if data.get("is_escalated") else None,
                is_campaign=data.get("is_campaign", False),
                campaign_score=data.get("campaign_score", 0.0),
                from_repeat_complainant=data.get("from_repeat_complainant", False),
                embedding=embedding,
                submitted_at=data["submitted_at"],
                analyzed_at=data["submitted_at"] + timedelta(minutes=2),
                resolved_at=data["submitted_at"] + timedelta(days=6)
                if data["status"] == "resolved" else None,
                created_at=data["submitted_at"],
            )
            db.add(appeal)
            appeals.append(appeal)
        await db.flush()

        # --- События обращений (видимая заявителю история) ---
        for appeal in appeals:
            db.add(
                AppealEvent(
                    appeal_id=appeal.id,
                    event_type="submitted",
                    actor="system",
                    comment="Обращение подано через портал",
                    created_at=appeal.submitted_at,
                )
            )
            if appeal.status in ("resolved", "in_progress", "pending_review"):
                db.add(
                    AppealEvent(
                        appeal_id=appeal.id,
                        event_type="status_changed",
                        actor="system",
                        details={"from": "new", "to": appeal.status},
                        created_at=appeal.submitted_at + timedelta(hours=2),
                    )
                )

        # --- Кластеры по сценариям ---
        scenario_appeals: dict[str, list[tuple[Appeal, dict]]] = {}
        for appeal, data in zip(appeals, appeal_data):
            scenario_appeals.setdefault(data["scenario"], []).append((appeal, data))

        for scenario, cluster_def in CLUSTER_SCENARIOS.items():
            members = scenario_appeals.get(scenario, [])
            if not members:
                continue
            member_appeals = [a for a, _ in members]
            cluster = AppealCluster(
                **cluster_def,
                appeal_count=len(member_appeals),
                requester_count=len({a.requester_id for a in member_appeals}),
                region_spread=dict(Counter(a.region for a in member_appeals)),
                first_seen=min(a.submitted_at for a in member_appeals),
            )
            db.add(cluster)
            await db.flush()
            for a in member_appeals:
                db.add(
                    ClusterMembership(
                        cluster_id=cluster.id,
                        appeal_id=a.id,
                        similarity_score=cluster_def["similarity_score"],
                    )
                )
                if scenario == "campaign_medicines":
                    a.campaign_cluster_id = cluster.id

        # --- Статистика заявителей и профиль повторного заявителя ---
        for key, requester in requesters.items():
            own = [a for a in appeals if a.requester_id == requester.id]
            requester.total_appeals = len(own)
            requester.resolved_appeals = sum(1 for a in own if a.status == "resolved")
            requester.rejected_appeals = sum(1 for a in own if a.status == "rejected")
            requester.first_appeal_date = min(a.submitted_at for a in own)
            requester.last_appeal_date = max(a.submitted_at for a in own)
            topics = Counter(a.category for a in own)
            requester.top_topics = [t for t, _ in topics.most_common(3)]
            requester.top_regions = list({a.region for a in own})[:3]
            requester.behavior_stats = {
                "avg_per_month": round(len(own) / 6, 2),
                "top_topic_share": round(topics.most_common(1)[0][1] / len(own), 2),
            }

        repeat = requesters.get("repeat_patient_1")
        if repeat is not None:
            repeat.category = "chronic_complainant"
            repeat.category_score = 0.78
            repeat.repeat_score = 0.78
            repeat.is_repeat_complainant = True

        # --- Проекты ответов ---
        draft_statuses = ["draft", "reviewed", "approved"]
        draft_count = 0
        for i, (appeal, data) in enumerate(zip(appeals, appeal_data)):
            if data["status"] in ("pending_review", "in_progress", "resolved") and i % 2 == 0:
                db.add(
                    DraftResponse(
                        appeal_id=appeal.id,
                        draft_text=build_draft_text(data),
                        legal_references=[
                            {"document": reg}
                            for reg in MEDICAL_KNOWLEDGE_BASE.get(
                                data["category"], MEDICAL_KNOWLEDGE_BASE["other"]
                            )["regulations"]
                        ],
                        confidence_score=0.74,
                        status=draft_statuses[i % len(draft_statuses)],
                        generation_model="seed-synthetic",
                        generation_time_ms=1200,
                        created_at=appeal.submitted_at + timedelta(minutes=3),
                    )
                )
                draft_count += 1

        # --- Журнал аудита: запуски агентов по каждому обращению ---
        for appeal in appeals:
            for agent in ("agent3", "agent1", "agent5", "agent2", "agent4"):
                db.add(
                    AuditLog(
                        actor=f"agent:{agent}",
                        action="agent_run",
                        entity_type="appeal",
                        entity_id=appeal.id,
                        details={"seed": True},
                        created_at=appeal.analyzed_at,
                    )
                )
        db.add(
            AuditLog(
                actor="system",
                action="seed_loaded",
                entity_type="system",
                details={"appeals": len(appeals), "synthetic": True},
            )
        )

        # --- Посты соцсетей ---
        for post in build_social_posts():
            db.add(SocialPost(**post))

        await db.commit()
        print(
            f"Готово: {len(appeals)} обращений, {len(requesters)} заявителей, "
            f"{len(CLUSTER_SCENARIOS)} кластера, {draft_count} проектов ответов, "
            f"50 постов соцсетей, {len(DEMO_SOURCES)} источников."
        )


if __name__ == "__main__":
    asyncio.run(seed())
