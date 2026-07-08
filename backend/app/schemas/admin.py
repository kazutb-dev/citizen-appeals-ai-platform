"""Схемы админ-панели: агенты, социальные источники, интеграции, база знаний."""
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

# === AI-агенты ===


class AgentSettingOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    agent_key: str
    display_name: str
    description: str | None = None
    is_enabled: bool
    config: dict
    prompt_template: str | None = None
    updated_at: datetime


class AgentSettingUpdate(BaseModel):
    is_enabled: bool | None = None
    config: dict | None = None
    prompt_template: str | None = None  # пустая строка → сброс к промпту по умолчанию


# === Социальные источники ===

VALID_PLATFORMS = {"instagram", "telegram", "facebook", "tiktok", "youtube", "vk", "x"}


class SocialSourceCreate(BaseModel):
    name: str = Field(min_length=2, max_length=200)
    platform: str
    url: str | None = Field(default=None, max_length=500)
    credentials: dict = Field(default_factory=dict)
    polling_interval_minutes: int = Field(default=30, ge=5, le=1440)
    is_enabled: bool = True


class SocialSourceUpdate(BaseModel):
    name: str | None = None
    url: str | None = None
    credentials: dict | None = None
    polling_interval_minutes: int | None = Field(default=None, ge=5, le=1440)
    is_enabled: bool | None = None


class SocialSourceOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    platform: str
    url: str | None = None
    has_credentials: bool = False
    polling_interval_minutes: int
    is_enabled: bool
    last_polled_at: datetime | None = None
    last_status: str
    last_error: str | None = None
    created_at: datetime


# === Интеграции ===


class IntegrationConfigIn(BaseModel):
    """Настройка интеграции Instagram: config — открытые параметры, secrets — ключи."""

    app_id: str | None = None
    business_account_id: str | None = None
    app_secret: str | None = None
    access_token: str | None = None
    refresh_token: str | None = None


class IntegrationOut(BaseModel):
    provider: str
    config: dict
    secrets_masked: dict  # {"app_secret": "••••1234"} — значения никогда не отдаются
    status: str
    token_expires_at: datetime | None = None
    last_health_check_at: datetime | None = None
    last_health_status: str | None = None


# === База знаний ===


class KnowledgeDocumentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    doc_type: str
    department_id: int | None = None
    filename: str | None = None
    status: str
    error: str | None = None
    chunk_count: int
    created_at: datetime


# === Подразделения ===


class DepartmentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    short_name: str | None = None
    code: str | None = None
    department_type: str
    categories: list[str] | None = None
    contact_email: str | None = None
