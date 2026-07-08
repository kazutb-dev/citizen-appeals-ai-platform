"""Оркестратор пяти агентов.

Запускается ТОЛЬКО из фонового воркера (arq) — никогда внутри синхронного
API-запроса. Порядок: embeddings → Агент 3 (дубликаты) → Агент 1 (эскалация)
→ Агент 5 (повторные заявители) → Агент 2 (кампании) → Агент 4 (проект ответа).

Каждый агент можно выключить из админ-панели (agent_settings.is_enabled) —
тогда шаг пропускается со статусом "skipped".

progress — необязательный async-callback (agent, status, payload) для живой
трансляции хода анализа (используется агент-лабораторией через Redis pub/sub).
"""
import logging
from collections.abc import Awaitable, Callable
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.agents import (
    agent1_critical,
    agent2_campaigns,
    agent3_duplicates,
    agent4_responses,
    agent5_repeat,
    agent_config,
    embedding_service,
    medical_agents,
)
from app.agents.llm_client import current_model
from app.config import settings
from app.core.audit import record_audit
from app.core.events import add_appeal_event, notify_requester
from app.core.i18n import detect_language
from app.models.appeal import Appeal
from app.models.draft import DraftResponse

logger = logging.getLogger(__name__)

ProgressCallback = Callable[[str, str, dict], Awaitable[None]]


async def _noop_progress(agent: str, status: str, payload: dict) -> None:
    return None


async def get_appeal(db: AsyncSession, appeal_id: int) -> Appeal:
    stmt = (
        select(Appeal)
        .options(selectinload(Appeal.requester))
        .where(Appeal.id == appeal_id)
    )
    appeal = (await db.execute(stmt)).scalar_one_or_none()
    if appeal is None:
        raise ValueError(f"Обращение #{appeal_id} не найдено")
    return appeal


async def update_status(db: AsyncSession, appeal_id: int, status: str) -> None:
    appeal = await get_appeal(db, appeal_id)
    appeal.status = status
    await db.flush()


async def log_agent_run(
    db: AsyncSession, appeal_id: int, agent: str, result
) -> None:
    await record_audit(
        db,
        action="agent_run",
        entity_type="appeal",
        entity_id=appeal_id,
        actor=f"agent:{agent}",
        details=result.model_dump(mode="json"),
    )


async def orchestrate(
    appeal_id: int,
    db: AsyncSession,
    progress: ProgressCallback = _noop_progress,
) -> dict:
    """Главная функция оркестрации всех агентов."""
    appeal = await get_appeal(db, appeal_id)
    await update_status(db, appeal_id, "analyzing")
    await add_appeal_event(db, appeal_id, "analysis_started", is_public=False)
    results: dict = {}

    # Шаг 1: Embeddings (нужны всем агентам)
    await progress("embedding", "running", {})
    if appeal.embedding is None:
        appeal.embedding = await embedding_service.encode(appeal.text)
        await db.flush()
    await progress("embedding", "done", {})

    # Шаг 2: Агент 3 — дубликаты
    if await agent_config.is_enabled(db, "agent3"):
        await progress("agent3", "running", {})
        dup_result = await agent3_duplicates.analyze(appeal, db)
        results["agent3"] = dup_result.model_dump()
        if dup_result.is_duplicate:
            appeal.is_duplicate = True
            appeal.duplicate_of_id = dup_result.duplicate_of_id
            appeal.duplicate_score = dup_result.score
            await update_status(db, appeal_id, "duplicate")
        await log_agent_run(db, appeal_id, "agent3", dup_result)
        await progress("agent3", "done", results["agent3"])
    else:
        await progress("agent3", "skipped", {})
    # Всё равно запускаем остальных агентов для полного профиля

    # Шаг 3: Агент 1 — эскалация руководству
    if await agent_config.is_enabled(db, "agent1"):
        await progress("agent1", "running", {})
        critical_result = await agent1_critical.analyze(appeal, db)
        results["agent1"] = critical_result.model_dump()
        appeal.risk_level = critical_result.risk_level
        appeal.risk_score = critical_result.risk_score
        appeal.risk_reasons = critical_result.risk_reasons
        appeal.tags = critical_result.tags
        if critical_result.escalate:
            appeal.is_escalated = True
            appeal.escalation_level = critical_result.escalation_level
            appeal.escalation_reason = critical_result.escalation_reason
            appeal.escalated_at = datetime.utcnow()
            await update_status(db, appeal_id, "escalated")
            await record_audit(
                db,
                action="appeal_escalated",
                entity_type="appeal",
                entity_id=appeal_id,
                actor="agent:agent1",
                details={"level": critical_result.escalation_level},
            )
            await add_appeal_event(
                db, appeal_id, "escalated",
                actor="agent:agent1",
                details={"level": critical_result.escalation_level},
                is_public=False,
            )
        await log_agent_run(db, appeal_id, "agent1", critical_result)
        await progress("agent1", "done", results["agent1"])
    else:
        await progress("agent1", "skipped", {})

    # Шаг 4: Агент 5 — повторные заявители
    if await agent_config.is_enabled(db, "agent5"):
        await progress("agent5", "running", {})
        repeat_result = await agent5_repeat.analyze(appeal.requester, db)
        results["agent5"] = repeat_result.model_dump()
        if appeal.requester is not None:
            appeal.requester.repeat_score = repeat_result.score
            appeal.requester.category = repeat_result.category
            appeal.requester.is_repeat_complainant = repeat_result.is_repeat_complainant
            appeal.requester.category_score = repeat_result.score
            appeal.requester.category_updated_at = datetime.utcnow()
        appeal.from_repeat_complainant = repeat_result.is_repeat_complainant
        await log_agent_run(db, appeal_id, "agent5", repeat_result)
        await progress("agent5", "done", results["agent5"])
    else:
        await progress("agent5", "skipped", {})

    # Шаг 5: Агент 2 — кампании
    if await agent_config.is_enabled(db, "agent2"):
        await progress("agent2", "running", {})
        campaign_result = await agent2_campaigns.analyze(appeal, db)
        results["agent2"] = campaign_result.model_dump()
        if campaign_result.is_campaign:
            appeal.is_campaign = True
            appeal.campaign_score = campaign_result.score
            appeal.campaign_cluster_id = campaign_result.cluster_id
        await log_agent_run(db, appeal_id, "agent2", campaign_result)
        await progress("agent2", "done", results["agent2"])
    else:
        await progress("agent2", "skipped", {})

    # Шаг 6: Агент 4 — генерация проекта ответа
    if await agent_config.is_enabled(db, "agent4"):
        await progress("agent4", "running", {})
        # Отвечаем гражданину на языке его обращения (kk/ru/en).
        draft_result = await agent4_responses.generate(
            appeal, db, lang=detect_language(appeal.text)
        )
        if draft_result:
            results["agent4"] = {
                "confidence": draft_result.confidence,
                "legal_refs": draft_result.legal_refs,
                "generation_time_ms": draft_result.generation_time_ms,
            }
            existing_draft = (
                await db.execute(
                    select(DraftResponse).where(DraftResponse.appeal_id == appeal_id)
                )
            ).scalar_one_or_none()
            if existing_draft is None:
                db.add(
                    DraftResponse(
                        appeal_id=appeal_id,
                        draft_text=draft_result.text,
                        legal_references=draft_result.legal_refs,
                        confidence_score=draft_result.confidence,
                        generation_model=current_model(),
                        generation_time_ms=draft_result.generation_time_ms,
                    )
                )
            else:
                existing_draft.draft_text = draft_result.text
                existing_draft.legal_references = draft_result.legal_refs
                existing_draft.confidence_score = draft_result.confidence
                existing_draft.generation_time_ms = draft_result.generation_time_ms
            await add_appeal_event(
                db, appeal_id, "response_drafted", actor="agent:agent4", is_public=False
            )
        await progress("agent4", "done", results.get("agent4", {}))
    else:
        await progress("agent4", "skipped", {})

    # Шаг 7: Агент 6 — лекарственное обеспечение (→ Аптека)
    if await agent_config.is_enabled(db, "agent6"):
        await progress("agent6", "running", {})
        ai_result = await medical_agents.medicine_supply_analyze(appeal, db)
        results["agent6"] = ai_result.model_dump()
        if ai_result.flagged:
            appeal.tags = list(dict.fromkeys((appeal.tags or []) + ["лекарственное обеспечение"]))
        await log_agent_run(db, appeal_id, "agent6", ai_result)
        await progress("agent6", "done", results["agent6"])
    else:
        await progress("agent6", "skipped", {})

    # Шаг 8: Агент 7 — качество медицинской помощи (→ Служба качества)
    if await agent_config.is_enabled(db, "agent7"):
        await progress("agent7", "running", {})
        fac_result = await medical_agents.care_quality_analyze(appeal, db)
        results["agent7"] = fac_result.model_dump()
        if fac_result.flagged:
            appeal.tags = list(dict.fromkeys((appeal.tags or []) + ["качество медпомощи"]))
        await log_agent_run(db, appeal_id, "agent7", fac_result)
        await progress("agent7", "done", results["agent7"])
    else:
        await progress("agent7", "skipped", {})

    # Шаг 9: Агент 8 — санитарно-эпидемиологический контроль (→ Санэпид)
    if await agent_config.is_enabled(db, "agent8"):
        await progress("agent8", "running", {})
        infra_result = await medical_agents.sanitary_epid_analyze(appeal, db)
        results["agent8"] = infra_result.model_dump()
        if infra_result.flagged:
            appeal.tags = list(dict.fromkeys((appeal.tags or []) + ["санитария"]))
        await log_agent_run(db, appeal_id, "agent8", infra_result)
        await progress("agent8", "done", results["agent8"])
    else:
        await progress("agent8", "skipped", {})

    # Финальный статус
    if not appeal.is_escalated and not appeal.is_duplicate:
        await update_status(db, appeal_id, "pending_review")

    appeal.analyzed_at = datetime.utcnow()
    await add_appeal_event(db, appeal_id, "analysis_done", is_public=False)
    await notify_requester(
        db,
        appeal,
        type="appeal_status",
        title="Обращение принято в работу",
        body=f"Ваше обращение «{appeal.title[:120]}» прошло первичную обработку и передано в работу.",
    )
    await db.commit()
    await progress("orchestrator", "finished", {"appeal_id": appeal_id})
    logger.info("Анализ обращения #%s завершён", appeal_id)
    return results
