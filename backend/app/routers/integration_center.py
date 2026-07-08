"""Integration Center — каталог интеграций, mock-тест соединения, приём/отправка."""
from datetime import datetime

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel

from app.core.exceptions import NotFoundError
from app.core.permissions import Role, require_role
from app.integrations import providers
from app.models.user import User

router = APIRouter(prefix="/integration-center", tags=["integration-center"])


class ProviderOut(BaseModel):
    key: str
    name: str
    kind: str
    direction: str
    description: str
    capabilities: list[str]
    mode: str
    status: str


class MessageOut(BaseModel):
    external_id: str
    channel: str
    author: str
    text: str
    received_at: datetime
    category_hint: str | None = None
    meta: dict = {}


class SendRequest(BaseModel):
    to: str
    text: str


@router.get("/catalog", response_model=list[ProviderOut])
async def catalog(user: User = Depends(require_role(Role.OPERATOR))) -> list[ProviderOut]:
    return [ProviderOut(**vars(p)) for p in providers.list_providers()]


@router.post("/{key}/test")
async def test_connection(
    key: str, user: User = Depends(require_role(Role.ADMIN))
) -> dict:
    result = providers.test_connection(key)
    if not result["ok"]:
        raise NotFoundError(result["message"])
    return result


@router.get("/{key}/sample", response_model=list[MessageOut])
async def sample_inbound(
    key: str,
    limit: int = Query(5, ge=1, le=20),
    user: User = Depends(require_role(Role.ANALYST)),
) -> list[MessageOut]:
    if providers.get_provider(key) is None:
        raise NotFoundError(f"Неизвестный провайдер: {key}")
    return [MessageOut(**vars(m)) for m in providers.mock_fetch(key, limit)]


@router.post("/{key}/send")
async def send_outbound(
    key: str,
    payload: SendRequest,
    user: User = Depends(require_role(Role.OPERATOR)),
) -> dict:
    result = providers.mock_send(key, payload.to, payload.text)
    if not result["ok"]:
        raise NotFoundError(result["message"])
    return result
