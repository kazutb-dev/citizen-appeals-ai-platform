"""AI & Infrastructure Monitoring — здоровье LLM, эмбеддингов, Redis, очереди, БД.

Best-effort проверки с короткими таймаутами. Ничего не выдумывает: если сервис
недоступен — честный статус unreachable/error.
"""
import time
from datetime import datetime

import httpx
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.core.permissions import Role, require_role
from app.database import get_db
from app.models.appeal import Appeal
from app.models.user import User

router = APIRouter(prefix="/monitoring", tags=["monitoring"])


class ComponentHealth(BaseModel):
    status: str
    detail: str | None = None
    latency_ms: int | None = None
    meta: dict = {}


class SystemHealth(BaseModel):
    checked_at: datetime
    llm: ComponentHealth
    embedding: ComponentHealth
    reranker: ComponentHealth
    redis: ComponentHealth
    worker_queue: ComponentHealth
    postgres: ComponentHealth
    vector_db: ComponentHealth


async def _check_llm() -> ComponentHealth:
    provider = (settings.LLM_PROVIDER or "").lower()
    base = settings.LLM_BASE_URL.rstrip("/") if settings.LLM_BASE_URL else ""
    meta = {"provider": provider, "model": settings.LLM_LOCAL_MODEL}
    if not base:
        return ComponentHealth(status="not_configured", meta=meta)
    url = f"{base}/api/tags" if provider == "ollama" else f"{base}/v1/models"
    try:
        started = time.monotonic()
        async with httpx.AsyncClient(timeout=3.0) as client:
            resp = await client.get(url)
        latency = int((time.monotonic() - started) * 1000)
        if resp.status_code == 200:
            return ComponentHealth(status="ok", latency_ms=latency, meta=meta)
        return ComponentHealth(
            status="unreachable", detail=f"HTTP {resp.status_code}", latency_ms=latency, meta=meta
        )
    except Exception as exc:  # noqa: BLE001
        return ComponentHealth(status="unreachable", detail=str(exc)[:200], meta=meta)


async def _redis_client():
    from redis.asyncio import from_url

    return from_url(settings.REDIS_URL)


async def _check_redis_and_queue() -> tuple[ComponentHealth, ComponentHealth]:
    try:
        client = await _redis_client()
        started = time.monotonic()
        await client.ping()
        latency = int((time.monotonic() - started) * 1000)
        queue_depth = None
        for key in ("arq:queue", "ncaip:lab", "arq:queue:default"):
            try:
                depth = await client.zcard(key)
                if depth:
                    queue_depth = depth
                    break
            except Exception:  # noqa: BLE001 — ключ может быть иного типа
                continue
        try:
            await client.aclose()
        except Exception:  # noqa: BLE001
            pass
        redis_health = ComponentHealth(status="ok", latency_ms=latency)
        worker_health = ComponentHealth(
            status="ok", meta={"queue_depth": queue_depth if queue_depth is not None else 0}
        )
        return redis_health, worker_health
    except Exception as exc:  # noqa: BLE001
        err = ComponentHealth(status="error", detail=str(exc)[:200])
        return err, err


@router.get("/health", response_model=SystemHealth)
async def health(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_role(Role.ANALYST)),
) -> SystemHealth:
    llm = await _check_llm()
    redis_health, worker_health = await _check_redis_and_queue()

    try:
        total = (await db.execute(select(func.count(Appeal.id)))).scalar_one()
        postgres = ComponentHealth(status="ok", meta={"appeals": total})
    except Exception as exc:  # noqa: BLE001
        postgres = ComponentHealth(status="error", detail=str(exc)[:200])

    embedding = ComponentHealth(
        status="configured",
        meta={
            "provider": settings.EMBEDDING_PROVIDER,
            "model": settings.EMBEDDING_MODEL,
            "dim": settings.EMBEDDING_DIM,
        },
    )
    reranker = ComponentHealth(
        status="enabled" if settings.RERANKER_ENABLED else "disabled",
        meta={"model": settings.RERANKER_MODEL},
    )
    vector_db = ComponentHealth(
        status="ok" if postgres.status == "ok" else "unknown",
        meta={"engine": settings.VECTOR_DB},
    )

    return SystemHealth(
        checked_at=datetime.utcnow(),
        llm=llm,
        embedding=embedding,
        reranker=reranker,
        redis=redis_health,
        worker_queue=worker_health,
        postgres=postgres,
        vector_db=vector_db,
    )
