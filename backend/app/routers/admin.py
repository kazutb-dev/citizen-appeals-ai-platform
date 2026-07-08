"""Админ-панель: AI-агенты, социальные источники, интеграции, база знаний,
пользователи и роли. Все эндпоинты — только для роли admin.
"""
import re
import uuid
from datetime import datetime
from pathlib import Path

import aiofiles
from fastapi import APIRouter, Depends, Query, Request, UploadFile
from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.agents import agent_config
from app.config import settings
from app.core.audit import record_audit
from app.core.exceptions import ConflictError, NotFoundError
from app.core.permissions import Role, require_role
from app.database import get_db
from app.integrations import instagram
from app.models.agent_setting import AgentSetting
from app.models.department import Department
from app.models.integration import Integration
from app.models.knowledge import KnowledgeDocument
from app.models.social import SocialSource
from app.models.user import User
from app.schemas.admin import (
    VALID_PLATFORMS,
    AgentSettingOut,
    AgentSettingUpdate,
    DepartmentOut,
    IntegrationConfigIn,
    IntegrationOut,
    KnowledgeDocumentOut,
    SocialSourceCreate,
    SocialSourceOut,
    SocialSourceUpdate,
)
from app.schemas.user import UserAdminUpdate, UserOut

router = APIRouter(prefix="/admin", tags=["admin"])

VALID_ROLES = {"admin", "analyst", "operator", "viewer", "requester"}
VALID_DOC_TYPES = {"regulation", "policy", "academic_rule", "handbook", "hr_policy", "procedure"}
ALLOWED_KNOWLEDGE_TYPES = {
    "application/pdf": ".pdf",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document": ".docx",
    "text/plain": ".txt",
    "text/markdown": ".md",
}


# ============================================================
# AI-агенты
# ============================================================


@router.get("/agents", response_model=list[AgentSettingOut])
async def list_agents(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_role(Role.ADMIN)),
) -> list[AgentSetting]:
    settings_list = await agent_config.ensure_defaults(db)
    await db.commit()
    return settings_list


@router.put("/agents/{agent_key}", response_model=AgentSettingOut)
async def update_agent(
    agent_key: str,
    payload: AgentSettingUpdate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_role(Role.ADMIN)),
) -> AgentSetting:
    await agent_config.ensure_defaults(db)
    setting = await agent_config.get_setting(db, agent_key)
    if setting is None:
        raise NotFoundError(f"Агент {agent_key} не найден")

    changes: dict = {}
    if payload.is_enabled is not None:
        setting.is_enabled = payload.is_enabled
        changes["is_enabled"] = payload.is_enabled
    if payload.config is not None:
        setting.config = payload.config
        changes["config"] = "updated"
    if payload.prompt_template is not None:
        setting.prompt_template = payload.prompt_template or None
        changes["prompt_template"] = "custom" if payload.prompt_template else "default"
    setting.updated_by_id = user.id

    await record_audit(
        db, action="agent_setting_updated", entity_type="agent_setting",
        entity_id=setting.id, user_id=user.id, actor=user.email,
        details={"agent": agent_key, **changes},
    )
    await db.commit()
    return setting


# ============================================================
# Социальные источники
# ============================================================


def _source_out(source: SocialSource) -> SocialSourceOut:
    out = SocialSourceOut.model_validate(source)
    out.has_credentials = bool(source.credentials)
    return out


@router.get("/social-sources", response_model=list[SocialSourceOut])
async def list_social_sources(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_role(Role.ADMIN)),
) -> list[SocialSourceOut]:
    rows = (
        await db.execute(select(SocialSource).order_by(SocialSource.id))
    ).scalars().all()
    return [_source_out(s) for s in rows]


@router.post("/social-sources", response_model=SocialSourceOut, status_code=201)
async def create_social_source(
    payload: SocialSourceCreate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_role(Role.ADMIN)),
) -> SocialSourceOut:
    if payload.platform not in VALID_PLATFORMS:
        raise ConflictError(f"Недопустимая платформа: {payload.platform}")
    source = SocialSource(
        name=payload.name,
        platform=payload.platform,
        url=payload.url,
        credentials=payload.credentials,
        polling_interval_minutes=payload.polling_interval_minutes,
        is_enabled=payload.is_enabled,
    )
    db.add(source)
    await db.flush()
    await record_audit(
        db, action="social_source_created", entity_type="social_source",
        entity_id=source.id, user_id=user.id, actor=user.email,
        details={"name": source.name, "platform": source.platform},
    )
    await db.commit()
    return _source_out(source)


@router.put("/social-sources/{source_id}", response_model=SocialSourceOut)
async def update_social_source(
    source_id: int,
    payload: SocialSourceUpdate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_role(Role.ADMIN)),
) -> SocialSourceOut:
    source = (
        await db.execute(select(SocialSource).where(SocialSource.id == source_id))
    ).scalar_one_or_none()
    if source is None:
        raise NotFoundError("Источник не найден")

    for field in ("name", "url", "polling_interval_minutes", "is_enabled"):
        value = getattr(payload, field)
        if value is not None:
            setattr(source, field, value)
    if payload.credentials is not None:
        source.credentials = payload.credentials
    await record_audit(
        db, action="social_source_updated", entity_type="social_source",
        entity_id=source.id, user_id=user.id, actor=user.email,
    )
    await db.commit()
    return _source_out(source)


@router.delete("/social-sources/{source_id}")
async def delete_social_source(
    source_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_role(Role.ADMIN)),
) -> dict:
    source = (
        await db.execute(select(SocialSource).where(SocialSource.id == source_id))
    ).scalar_one_or_none()
    if source is None:
        raise NotFoundError("Источник не найден")
    await record_audit(
        db, action="social_source_deleted", entity_type="social_source",
        entity_id=source.id, user_id=user.id, actor=user.email,
        details={"name": source.name, "platform": source.platform},
    )
    await db.delete(source)
    await db.commit()
    return {"detail": "Источник удалён"}


@router.post("/social-sources/{source_id}/poll")
async def poll_social_source(
    source_id: int,
    request: Request,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_role(Role.ADMIN)),
) -> dict:
    """Ручной запуск опроса источника (выполняется в фоновом воркере)."""
    source = (
        await db.execute(select(SocialSource).where(SocialSource.id == source_id))
    ).scalar_one_or_none()
    if source is None:
        raise NotFoundError("Источник не найден")
    await request.app.state.arq.enqueue_job("poll_social_source", source_id)
    return {"detail": "Опрос поставлен в очередь", "source_id": source_id}


# ============================================================
# Интеграции (Instagram Graph API)
# ============================================================

SECRET_KEYS = ("app_secret", "access_token", "refresh_token")


def _mask(value: str) -> str:
    return "••••" + value[-4:] if len(value) > 4 else "••••"


async def _get_or_create_integration(db: AsyncSession, provider: str) -> Integration:
    integration = (
        await db.execute(select(Integration).where(Integration.provider == provider))
    ).scalar_one_or_none()
    if integration is None:
        integration = Integration(provider=provider, config={}, secrets={})
        db.add(integration)
        await db.flush()
    return integration


def _integration_out(integration: Integration) -> IntegrationOut:
    return IntegrationOut(
        provider=integration.provider,
        config=integration.config or {},
        secrets_masked={
            k: _mask(v) for k, v in (integration.secrets or {}).items() if v
        },
        status=integration.status,
        token_expires_at=integration.token_expires_at,
        last_health_check_at=integration.last_health_check_at,
        last_health_status=integration.last_health_status,
    )


@router.get("/integrations", response_model=list[IntegrationOut])
async def list_integrations(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_role(Role.ADMIN)),
) -> list[IntegrationOut]:
    instagram_integration = await _get_or_create_integration(db, "instagram")
    await db.commit()
    return [_integration_out(instagram_integration)]


@router.get("/integrations/instagram", response_model=IntegrationOut)
async def get_instagram(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_role(Role.ADMIN)),
) -> IntegrationOut:
    integration = await _get_or_create_integration(db, "instagram")
    await db.commit()
    return _integration_out(integration)


@router.put("/integrations/instagram", response_model=IntegrationOut)
async def update_instagram(
    payload: IntegrationConfigIn,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_role(Role.ADMIN)),
) -> IntegrationOut:
    integration = await _get_or_create_integration(db, "instagram")
    config = dict(integration.config or {})
    secrets = dict(integration.secrets or {})

    if payload.app_id is not None:
        config["app_id"] = payload.app_id
    if payload.business_account_id is not None:
        config["business_account_id"] = payload.business_account_id
    for key in SECRET_KEYS:
        value = getattr(payload, key)
        if value:  # пустые значения не затирают сохранённые секреты
            secrets[key] = value

    integration.config = config
    integration.secrets = secrets
    if config.get("app_id") and secrets.get("app_secret"):
        if integration.status == "not_configured":
            integration.status = "configured"
    await record_audit(
        db, action="integration_updated", entity_type="integration",
        entity_id=integration.id, user_id=user.id, actor=user.email,
        details={"provider": "instagram",
                 "fields": [k for k in ("app_id", "business_account_id", *SECRET_KEYS)
                            if getattr(payload, k)]},
    )
    await db.commit()
    return _integration_out(integration)


@router.get("/integrations/instagram/oauth-url")
async def instagram_oauth_url(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_role(Role.ADMIN)),
) -> dict:
    """URL авторизации OAuth. Redirect URI ведёт на страницу интеграций
    фронтенда — она передаёт полученный code в /oauth/exchange.
    """
    integration = await _get_or_create_integration(db, "instagram")
    config = dict(integration.config or {})
    if not config.get("app_id"):
        raise ConflictError("Сначала укажите App ID")

    state = instagram.generate_state()
    redirect_uri = f"{settings.PUBLIC_BASE_URL.rstrip('/')}/admin/integrations"
    config["oauth_state"] = state
    config["redirect_uri"] = redirect_uri
    integration.config = config
    await db.commit()
    return {
        "oauth_url": instagram.build_oauth_url(config["app_id"], redirect_uri, state),
        "redirect_uri": redirect_uri,
    }


class OAuthExchangeIn(BaseModel):
    code: str
    state: str


@router.post("/integrations/instagram/oauth/exchange", response_model=IntegrationOut)
async def instagram_oauth_exchange(
    payload: OAuthExchangeIn,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_role(Role.ADMIN)),
) -> IntegrationOut:
    integration = await _get_or_create_integration(db, "instagram")
    config = dict(integration.config or {})
    secrets = dict(integration.secrets or {})

    if not config.get("app_id") or not secrets.get("app_secret"):
        raise ConflictError("Сначала укажите App ID и App Secret")
    if payload.state != config.get("oauth_state"):
        raise ConflictError("Неверный state — начните авторизацию заново")

    try:
        token = await instagram.exchange_code(
            config["app_id"], secrets["app_secret"],
            config.get("redirect_uri", ""), payload.code,
        )
    except instagram.InstagramGraphError as exc:
        integration.status = "error"
        integration.last_health_status = str(exc)[:300]
        await db.commit()
        raise ConflictError(str(exc)) from exc

    secrets["access_token"] = token.access_token
    integration.secrets = secrets
    integration.token_expires_at = token.expires_at
    integration.status = "connected"
    config.pop("oauth_state", None)
    integration.config = config
    await record_audit(
        db, action="integration_connected", entity_type="integration",
        entity_id=integration.id, user_id=user.id, actor=user.email,
        details={"provider": "instagram"},
    )
    await db.commit()
    return _integration_out(integration)


@router.post("/integrations/instagram/health", response_model=IntegrationOut)
async def instagram_health(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_role(Role.ADMIN)),
) -> IntegrationOut:
    integration = await _get_or_create_integration(db, "instagram")
    config = integration.config or {}
    secrets = integration.secrets or {}
    integration.last_health_check_at = datetime.utcnow()

    if not (secrets.get("access_token") and secrets.get("app_secret")
            and config.get("business_account_id")):
        integration.last_health_status = (
            "Не настроено: нужны access_token, app_secret и business_account_id"
        )
        integration.status = (
            "configured" if config.get("app_id") else "not_configured"
        )
    else:
        try:
            info = await instagram.health_check(
                secrets["access_token"], secrets["app_secret"],
                config["business_account_id"],
            )
            integration.last_health_status = (
                f"OK: @{info.get('username')}, подписчиков {info.get('followers_count')}"
            )
            integration.status = "connected"
        except instagram.InstagramGraphError as exc:
            integration.last_health_status = str(exc)[:300]
            integration.status = "error"
    await db.commit()
    return _integration_out(integration)


# ============================================================
# База знаний
# ============================================================


@router.get("/knowledge", response_model=list[KnowledgeDocumentOut])
async def list_knowledge(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_role(Role.ADMIN)),
) -> list[KnowledgeDocument]:
    rows = (
        await db.execute(
            select(KnowledgeDocument).order_by(KnowledgeDocument.created_at.desc())
        )
    ).scalars().all()
    return list(rows)


@router.post("/knowledge/upload", response_model=KnowledgeDocumentOut, status_code=201)
async def upload_knowledge(
    request: Request,
    file: UploadFile,
    title: str = Query(min_length=3, max_length=300),
    doc_type: str = Query(default="regulation"),
    department_id: int | None = Query(default=None),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_role(Role.ADMIN)),
) -> KnowledgeDocument:
    """Загрузка документа; извлечение текста и эмбеддинги — в фоновом воркере."""
    if doc_type not in VALID_DOC_TYPES:
        raise ConflictError(f"Недопустимый тип документа: {doc_type}")
    if file.content_type not in ALLOWED_KNOWLEDGE_TYPES:
        raise ConflictError(
            f"Поддерживаются PDF, DOCX, TXT, MD; получен {file.content_type}"
        )

    max_bytes = settings.MAX_UPLOAD_MB * 1024 * 1024
    safe_name = re.sub(r"[^\w.\-]", "_", file.filename or "document")[:200]
    store_dir = Path(settings.UPLOAD_DIR) / "knowledge"
    store_dir.mkdir(parents=True, exist_ok=True)
    storage_path = store_dir / f"{uuid.uuid4().hex}_{safe_name}"

    size = 0
    async with aiofiles.open(storage_path, "wb") as out:
        while chunk := await file.read(1024 * 1024):
            size += len(chunk)
            if size > max_bytes:
                storage_path.unlink(missing_ok=True)
                raise ConflictError(f"Файл больше {settings.MAX_UPLOAD_MB} МБ")
            await out.write(chunk)

    document = KnowledgeDocument(
        title=title,
        doc_type=doc_type,
        department_id=department_id,
        filename=safe_name,
        storage_path=str(storage_path),
        status="processing",
        uploaded_by_id=user.id,
    )
    db.add(document)
    await db.flush()
    await record_audit(
        db, action="knowledge_uploaded", entity_type="knowledge_document",
        entity_id=document.id, user_id=user.id, actor=user.email,
        details={"title": title, "doc_type": doc_type, "size": size},
    )
    await db.commit()

    await request.app.state.arq.enqueue_job("process_knowledge_document", document.id)
    return document


@router.post("/knowledge/{document_id}/reprocess", response_model=KnowledgeDocumentOut)
async def reprocess_knowledge(
    document_id: int,
    request: Request,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_role(Role.ADMIN)),
) -> KnowledgeDocument:
    document = (
        await db.execute(
            select(KnowledgeDocument).where(KnowledgeDocument.id == document_id)
        )
    ).scalar_one_or_none()
    if document is None:
        raise NotFoundError("Документ не найден")
    document.status = "processing"
    document.error = None
    await db.commit()
    await request.app.state.arq.enqueue_job("process_knowledge_document", document_id)
    return document


@router.delete("/knowledge/{document_id}")
async def delete_knowledge(
    document_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_role(Role.ADMIN)),
) -> dict:
    document = (
        await db.execute(
            select(KnowledgeDocument).where(KnowledgeDocument.id == document_id)
        )
    ).scalar_one_or_none()
    if document is None:
        raise NotFoundError("Документ не найден")
    if document.storage_path:
        Path(document.storage_path).unlink(missing_ok=True)
    await record_audit(
        db, action="knowledge_deleted", entity_type="knowledge_document",
        entity_id=document.id, user_id=user.id, actor=user.email,
        details={"title": document.title},
    )
    await db.delete(document)  # чанки удаляются каскадом
    await db.commit()
    return {"detail": "Документ удалён"}


# ============================================================
# Пользователи и роли
# ============================================================


@router.get("/users", response_model=list[UserOut])
async def list_users(
    role: str | None = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_role(Role.ADMIN)),
) -> list[User]:
    stmt = select(User).order_by(User.id)
    if role:
        stmt = stmt.where(User.role == role)
    rows = (
        await db.execute(stmt.offset((page - 1) * page_size).limit(page_size))
    ).scalars().all()
    return list(rows)


@router.put("/users/{user_id}", response_model=UserOut)
async def update_user(
    user_id: int,
    payload: UserAdminUpdate,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(require_role(Role.ADMIN)),
) -> User:
    target = (
        await db.execute(select(User).where(User.id == user_id))
    ).scalar_one_or_none()
    if target is None:
        raise NotFoundError("Пользователь не найден")
    if payload.role is not None:
        if payload.role not in VALID_ROLES:
            raise ConflictError(f"Недопустимая роль: {payload.role}")
        if target.id == admin.id and payload.role != "admin":
            raise ConflictError("Нельзя понизить собственную роль администратора")
        target.role = payload.role
    if payload.is_active is not None:
        if target.id == admin.id and not payload.is_active:
            raise ConflictError("Нельзя деактивировать собственную учётную запись")
        target.is_active = payload.is_active
    if payload.department_id is not None:
        target.department_id = payload.department_id
    if payload.position is not None:
        target.position = payload.position
    await record_audit(
        db, action="user_updated", entity_type="user", entity_id=target.id,
        user_id=admin.id, actor=admin.email,
        details=payload.model_dump(exclude_none=True),
    )
    await db.commit()
    return target


# ============================================================
# Подразделения (справочник)
# ============================================================


@router.get("/departments", response_model=list[DepartmentOut])
async def list_departments(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_role(Role.ADMIN)),
) -> list[Department]:
    rows = (await db.execute(select(Department).order_by(Department.id))).scalars().all()
    return list(rows)
