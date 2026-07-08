from contextlib import asynccontextmanager

from arq import create_pool
from arq.connections import RedisSettings
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.routers import (
    admin,
    analytics,
    appeals,
    audit,
    auth,
    clusters,
    command_center,
    drafts,
    integration_center,
    intelligence,
    lab,
    meta,
    monitoring,
    notifications,
    requesters,
    social,
    tenants,
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Пул arq для постановки фоновых задач из API
    app.state.arq = await create_pool(RedisSettings.from_dsn(settings.REDIS_URL))
    yield
    await app.state.arq.close()


app = FastAPI(
    title="MedHubHAQ — AI-платформа обращений граждан в сфере здравоохранения",
    description=(
        "MedHubHAQ — единая платформа приёма, учёта, маршрутизации и анализа "
        "обращений пациентов и граждан по вопросам здравоохранения. AI-анализ "
        "(5 основных + 3 профильных агента), выявление дубликатов и кампаний, "
        "мониторинг соцсетей, RAG-база знаний и аналитика."
    ),
    version="3.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

for router in (
    auth.router,
    appeals.router,
    analytics.router,
    requesters.router,
    clusters.router,
    drafts.router,
    social.router,
    audit.router,
    lab.router,
    notifications.router,
    admin.router,
    meta.router,
    tenants.router,
    command_center.router,
    monitoring.router,
    integration_center.router,
    intelligence.router,
):
    app.include_router(router, prefix="/api")


@app.get("/api/health")
async def health() -> dict:
    return {"status": "ok"}
