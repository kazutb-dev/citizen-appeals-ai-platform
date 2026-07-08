"""Агент-лаборатория: анализ произвольного текста всеми агентами без сохранения в БД.

POST /lab/analyze ставит задачу в arq; воркер публикует события прогресса
в Redis-список, GET /lab/stream/{task_id} транслирует их через SSE.
"""
import json
import uuid

from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel, Field
from sse_starlette.sse import EventSourceResponse

from app.config import LAB_QUEUE_PREFIX
from app.core.i18n import resolve_language
from app.core.permissions import Role, require_role
from app.models.user import User

router = APIRouter(prefix="/lab", tags=["lab"])

STREAM_TIMEOUT_SECONDS = 300


class LabRequest(BaseModel):
    text: str = Field(min_length=10, max_length=10000)
    region: str = "Главный корпус"
    category: str = "other"


@router.post("/analyze")
async def analyze(
    payload: LabRequest,
    request: Request,
    user: User = Depends(require_role(Role.VIEWER)),
) -> dict:
    task_id = uuid.uuid4().hex
    await request.app.state.arq.enqueue_job(
        "lab_analyze", task_id, payload.text, payload.region, payload.category,
        resolve_language(request),
    )
    return {"task_id": task_id}


@router.get("/stream/{task_id}")
async def stream(
    task_id: str,
    request: Request,
    user: User = Depends(require_role(Role.VIEWER)),
) -> EventSourceResponse:
    redis = request.app.state.arq
    key = f"{LAB_QUEUE_PREFIX}{task_id}"

    async def event_generator():
        waited = 0.0
        while waited < STREAM_TIMEOUT_SECONDS:
            if await request.is_disconnected():
                return
            item = await redis.blpop(key, timeout=2)
            if item is None:
                waited += 2
                continue
            raw = item[1]
            event = json.loads(raw)
            yield {"event": "progress", "data": json.dumps(event, ensure_ascii=False)}
            if event.get("agent") == "orchestrator" and event.get("status") in (
                "finished",
                "error",
            ):
                return
        yield {
            "event": "progress",
            "data": json.dumps(
                {"agent": "orchestrator", "status": "error",
                 "payload": {"detail": "Таймаут ожидания результата"}},
                ensure_ascii=False,
            ),
        }

    return EventSourceResponse(event_generator())
