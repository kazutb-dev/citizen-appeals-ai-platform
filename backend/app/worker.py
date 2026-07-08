"""Фоновый воркер arq: оркестрация агентов, обработка документов базы знаний
и опрос социальных источников. Никакой AI-инференс не выполняется внутри
синхронных API-запросов — только здесь.
"""
import json
import logging
from datetime import datetime, timedelta

from arq import cron
from arq.connections import RedisSettings
from sqlalchemy import select

from app.agents import (
    agent1_critical,
    agent2_campaigns,
    agent3_duplicates,
    agent4_responses,
    agent5_repeat,
    embedding_service,
    medical_agents,
    orchestrator,
)
from app.agents.llm_client import complete_json
from app.config import LAB_QUEUE_PREFIX, settings
from app.database import async_session_factory
from app.integrations import adapters, instagram
from app.models.appeal import Appeal
from app.models.integration import Integration
from app.models.knowledge import KnowledgeChunk, KnowledgeDocument
from app.models.social import SocialPost, SocialSource

logger = logging.getLogger(__name__)

LAB_EVENT_TTL = 600  # секунд


async def analyze_appeal(ctx: dict, appeal_id: int) -> dict:
    """Полный конвейер агентов для сохранённого обращения."""
    async with async_session_factory() as db:
        return await orchestrator.orchestrate(appeal_id, db)


# ============================================================
# Агент-лаборатория
# ============================================================


async def _publish_lab_event(redis, task_id: str, agent: str, status: str, payload: dict):
    event = {
        "agent": agent,
        "status": status,
        "payload": payload,
        "ts": datetime.utcnow().isoformat(),
    }
    key = f"{LAB_QUEUE_PREFIX}{task_id}"
    await redis.rpush(key, json.dumps(event, ensure_ascii=False))
    await redis.expire(key, LAB_EVENT_TTL)


async def lab_analyze(ctx: dict, task_id: str, text: str, region: str, category: str, lang: str = "ru") -> dict:
    """Лабораторный анализ: все агенты на произвольном тексте, БЕЗ сохранения в БД.

    События прогресса публикуются в Redis-список — их читает SSE-эндпоинт.
    """
    redis = ctx["redis"]

    async def progress(agent: str, status: str, payload: dict) -> None:
        await _publish_lab_event(redis, task_id, agent, status, payload)

    results: dict = {}
    # Транзиентное обращение: в сессию не добавляется, в БД не попадает
    appeal = Appeal(
        title=text[:200],
        text=text,
        category=category,
        region=region,
        submitted_at=datetime.utcnow(),
    )

    async with async_session_factory() as db:
        try:
            await progress("embedding", "running", {})
            appeal.embedding = await embedding_service.encode(text)
            await progress("embedding", "done", {})

            await progress("agent3", "running", {})
            dup = await agent3_duplicates.analyze(appeal, db)
            results["agent3"] = dup.model_dump()
            await progress("agent3", "done", results["agent3"])

            await progress("agent1", "running", {})
            critical = await agent1_critical.analyze(appeal, db)
            results["agent1"] = critical.model_dump()
            await progress("agent1", "done", results["agent1"])

            await progress("agent5", "running", {})
            repeat = await agent5_repeat.analyze(None, db)
            results["agent5"] = repeat.model_dump()
            await progress("agent5", "done", results["agent5"])

            await progress("agent2", "running", {})
            campaign = await agent2_campaigns.analyze(appeal, db)
            results["agent2"] = campaign.model_dump()
            await progress("agent2", "done", results["agent2"])

            await progress("agent4", "running", {})
            draft = await agent4_responses.generate(appeal, db, lang=lang)
            results["agent4"] = (
                {
                    "text": draft.text,
                    "legal_refs": draft.legal_refs,
                    "confidence": draft.confidence,
                    "generation_time_ms": draft.generation_time_ms,
                }
                if draft
                else {}
            )
            await progress("agent4", "done", results["agent4"])

            await progress("agent6", "running", {})
            medicine = await medical_agents.medicine_supply_analyze(appeal, db)
            results["agent6"] = medicine.model_dump()
            await progress("agent6", "done", results["agent6"])

            await progress("agent7", "running", {})
            care = await medical_agents.care_quality_analyze(appeal, db)
            results["agent7"] = care.model_dump()
            await progress("agent7", "done", results["agent7"])

            await progress("agent8", "running", {})
            sanitary = await medical_agents.sanitary_epid_analyze(appeal, db)
            results["agent8"] = sanitary.model_dump()
            await progress("agent8", "done", results["agent8"])
        except Exception as exc:  # noqa: BLE001 — ошибку нужно доставить в SSE
            logger.exception("Ошибка лабораторного анализа %s", task_id)
            await progress("orchestrator", "error", {"detail": str(exc)})
            raise
        finally:
            # Лаборатория ничего не пишет в БД (Агент 2 мог создать кластер)
            await db.rollback()

    await progress("orchestrator", "finished", results)
    return results


# ============================================================
# База знаний: извлечение текста, чанки, эмбеддинги
# ============================================================

CHUNK_SIZE = 1200
CHUNK_OVERLAP = 150


def _extract_text(storage_path: str, filename: str) -> str:
    name = (filename or storage_path).lower()
    if name.endswith(".pdf"):
        from pypdf import PdfReader

        reader = PdfReader(storage_path)
        return "\n\n".join(page.extract_text() or "" for page in reader.pages)
    if name.endswith(".docx"):
        import docx

        document = docx.Document(storage_path)
        return "\n".join(p.text for p in document.paragraphs)
    with open(storage_path, encoding="utf-8", errors="replace") as f:
        return f.read()


def _split_chunks(text: str) -> list[str]:
    """Чанки ~CHUNK_SIZE символов с перекрытием, по границам абзацев."""
    paragraphs = [p.strip() for p in text.split("\n") if p.strip()]
    chunks: list[str] = []
    current = ""
    for para in paragraphs:
        if len(current) + len(para) + 1 > CHUNK_SIZE and current:
            chunks.append(current)
            current = current[-CHUNK_OVERLAP:] + "\n" + para
        else:
            current = f"{current}\n{para}" if current else para
    if current.strip():
        chunks.append(current)
    return [c for c in chunks if len(c) > 50]


async def process_knowledge_document(ctx: dict, document_id: int) -> dict:
    """Извлечь текст документа, разбить на чанки, посчитать эмбеддинги."""
    async with async_session_factory() as db:
        document = (
            await db.execute(
                select(KnowledgeDocument).where(KnowledgeDocument.id == document_id)
            )
        ).scalar_one_or_none()
        if document is None:
            return {"error": "not_found"}

        try:
            text = _extract_text(document.storage_path, document.filename or "")
            chunks = _split_chunks(text)
            if not chunks:
                raise ValueError("Не удалось извлечь текст из документа")

            embeddings = await embedding_service.encode_batch(chunks)

            # Заменить старые чанки
            for old in (
                await db.execute(
                    select(KnowledgeChunk).where(KnowledgeChunk.document_id == document_id)
                )
            ).scalars():
                await db.delete(old)
            for i, (chunk_text, emb) in enumerate(zip(chunks, embeddings)):
                db.add(
                    KnowledgeChunk(
                        document_id=document_id,
                        chunk_index=i,
                        text=chunk_text,
                        embedding=emb,
                    )
                )
            document.status = "ready"
            document.error = None
            document.chunk_count = len(chunks)
            await db.commit()
            logger.info("База знаний: документ #%s готов (%s чанков)", document_id, len(chunks))
            return {"chunks": len(chunks)}
        except Exception as exc:  # noqa: BLE001 — статус ошибки сохраняем в документе
            logger.exception("Ошибка обработки документа #%s", document_id)
            document.status = "failed"
            document.error = str(exc)[:1000]
            await db.commit()
            return {"error": str(exc)}


# ============================================================
# Социальный мониторинг
# ============================================================

SOCIAL_CLASSIFY_PROMPT = """
Ты — аналитик социального мониторинга упоминаний медицинской организации
(MedHubHAQ) в социальных сетях.

ПОСТ:
---
{post_text}
---

Определи:
- topic: краткая тема (до 60 символов, на русском)
- category: medicines | emergency | hospitalization | quality_of_care | access | medical_staff | diagnostics | preventive | financial | sanitary | documents | legal | other
- sentiment: positive | neutral | negative | alarming (alarming = угроза жизни/здоровью/репутации)
- risk_level: low | medium | high | critical
- region: регион РК, если упомянут (Астана, Алматы, Шымкент, …), иначе null
- tags: до 5 тегов на русском

Ответь СТРОГО в JSON:
{{"topic": "...", "category": "...", "sentiment": "...", "risk_level": "...", "region": null, "tags": []}}
"""


async def _classify_post(text: str) -> dict:
    try:
        return await complete_json(
            SOCIAL_CLASSIFY_PROMPT.format(post_text=text[:1500]), max_tokens=300
        )
    except Exception:  # noqa: BLE001 — пост сохраняем и без классификации
        logger.exception("Не удалось классифицировать пост соцсети")
        return {}


async def _fetch_for_source(db, source: SocialSource) -> list[adapters.FetchedPost]:
    if source.platform == "telegram":
        return await adapters.fetch_telegram_public(source.url or "")
    if source.platform == "youtube":
        return await adapters.fetch_youtube_rss(source.url or "")
    if source.platform == "vk":
        return await adapters.fetch_vk_wall(source.url or "", source.credentials or {})
    if source.platform == "instagram":
        integration = (
            await db.execute(
                select(Integration).where(Integration.provider == "instagram")
            )
        ).scalar_one_or_none()
        secrets = (integration.secrets or {}) if integration else {}
        config = (integration.config or {}) if integration else {}
        if (
            integration is not None
            and integration.status == "connected"
            and secrets.get("access_token")
            and config.get("business_account_id")
        ):
            media = await instagram.fetch_recent_media(
                secrets["access_token"], secrets["app_secret"],
                config["business_account_id"],
            )
            mentions = await instagram.fetch_mentions(
                secrets["access_token"], secrets["app_secret"],
                config["business_account_id"],
            )
            posts = []
            for item in media + mentions:
                caption = item.get("caption") or ""
                if not caption:
                    continue
                posts.append(
                    adapters.FetchedPost(
                        external_id=f"ig:{item['id']}",
                        text=caption[:4000],
                        url=item.get("permalink"),
                        posted_at=datetime.fromisoformat(
                            item["timestamp"].replace("+0000", "+00:00")
                        ).replace(tzinfo=None),
                        author=item.get("username") or source.name,
                        likes=item.get("like_count", 0),
                        comments=item.get("comments_count", 0),
                    )
                )
            return posts
        # Запасной вариант: публичный профиль (без логина и sessionid)
        return await adapters.fetch_instagram_public(source.url or "")
    raise adapters.AdapterError(
        f"Платформа «{source.platform}» требует партнёрского API-доступа: "
        "добавьте ключи в учётные данные источника (пока не настроено)"
    )


async def poll_social_source(ctx: dict, source_id: int) -> dict:
    """Опрос одного источника: загрузка постов, дедупликация, AI-классификация."""
    async with async_session_factory() as db:
        source = (
            await db.execute(select(SocialSource).where(SocialSource.id == source_id))
        ).scalar_one_or_none()
        if source is None:
            return {"error": "not_found"}

        source.last_polled_at = datetime.utcnow()
        try:
            fetched = await _fetch_for_source(db, source)
        except adapters.AdapterError as exc:
            source.last_status = "not_configured" if "не настроено" in str(exc) else "error"
            source.last_error = str(exc)[:1000]
            await db.commit()
            return {"error": str(exc)}
        except Exception as exc:  # noqa: BLE001 — статус ошибки сохраняем в источнике
            logger.exception("Ошибка опроса источника #%s", source_id)
            source.last_status = "error"
            source.last_error = str(exc)[:1000]
            await db.commit()
            return {"error": str(exc)}

        new_count = 0
        for post in fetched:
            if post.url:
                exists = (
                    await db.execute(
                        select(SocialPost.id).where(SocialPost.post_url == post.url)
                    )
                ).scalar_one_or_none()
                if exists:
                    continue
            classification = await _classify_post(post.text)
            embedding = await embedding_service.encode(post.text, prefix="passage")
            db.add(
                SocialPost(
                    platform=source.platform,
                    source_id=source.id,
                    source_account=post.author,
                    source_name=source.name,
                    post_url=post.url,
                    post_text=post.text,
                    post_date=post.posted_at,
                    views=post.views,
                    likes=post.likes,
                    comments=post.comments,
                    shares=post.shares,
                    topic=classification.get("topic"),
                    category=classification.get("category"),
                    region=classification.get("region"),
                    risk_level=classification.get("risk_level", "low"),
                    sentiment=classification.get("sentiment", "neutral"),
                    tags=classification.get("tags", []),
                    embedding=embedding,
                )
            )
            new_count += 1

        source.last_status = "ok"
        source.last_error = None
        await db.commit()
        logger.info("Источник #%s: %s новых постов", source_id, new_count)
        return {"new_posts": new_count}


async def poll_social_sources_cron(ctx: dict) -> dict:
    """Каждые 5 минут ставит в очередь источники, у которых подошёл интервал."""
    async with async_session_factory() as db:
        sources = (
            await db.execute(select(SocialSource).where(SocialSource.is_enabled.is_(True)))
        ).scalars().all()
        due = [
            s.id
            for s in sources
            if s.last_polled_at is None
            or datetime.utcnow() - s.last_polled_at
            >= timedelta(minutes=s.polling_interval_minutes)
        ]
    for source_id in due:
        await ctx["redis"].enqueue_job("poll_social_source", source_id)
    return {"queued": due}


class WorkerSettings:
    functions = [
        analyze_appeal,
        lab_analyze,
        process_knowledge_document,
        poll_social_source,
    ]
    cron_jobs = [
        cron(poll_social_sources_cron, minute=set(range(0, 60, 5)), run_at_startup=False),
    ]
    redis_settings = RedisSettings.from_dsn(settings.REDIS_URL)
    max_jobs = 4
    job_timeout = 600
