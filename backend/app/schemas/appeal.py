from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.requester import RequesterBrief


class AppealCreate(BaseModel):
    """Создание обращения оператором (от имени заявителя)."""

    title: str = Field(min_length=3, max_length=500)
    text: str = Field(min_length=10, max_length=20000)
    category: str
    subcategory: str | None = None
    region: str
    district: str | None = None
    requester_id: int | None = None
    # Либо существующий заявитель, либо данные нового
    requester_full_name: str | None = None
    requester_identifier: str | None = None  # хэшируется, в открытом виде не хранится
    requester_type: str | None = None
    affiliation: str | None = None
    external_id: str | None = None
    # Канал-источник и геолокация (единый учёт)
    source_channel: str | None = None
    latitude: float | None = None
    longitude: float | None = None
    location_name: str | None = None


class AppealSubmit(BaseModel):
    """Подача обращения пользователем портала (/submit)."""

    title: str = Field(min_length=3, max_length=500)
    text: str = Field(min_length=10, max_length=20000)
    category: str
    subcategory: str | None = None
    region: str
    district: str | None = None
    # Геолокация обязательна: без выбора места на карте обращение не принимается.
    # Границы — территория Республики Казахстан.
    latitude: float = Field(ge=40.0, le=56.0, description="Широта места (в пределах РК)")
    longitude: float = Field(ge=46.0, le=88.0, description="Долгота места (в пределах РК)")
    location_name: str | None = Field(default=None, max_length=300)


class AppealStatusUpdate(BaseModel):
    status: str
    comment: str | None = None


class AttachmentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    filename: str
    content_type: str | None = None
    size_bytes: int
    created_at: datetime


class AppealEventOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    event_type: str
    actor: str
    comment: str | None = None
    details: dict
    created_at: datetime


class AppealBrief(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    category: str
    subcategory: str | None = None
    region: str
    status: str
    risk_level: str
    risk_score: float
    is_escalated: bool
    is_campaign: bool
    is_duplicate: bool
    from_repeat_complainant: bool
    submitted_at: datetime
    requester: RequesterBrief | None = None
    # Единый учёт: канал-источник и геолокация (для карты обращений)
    source_channel: str | None = None
    latitude: float | None = None
    longitude: float | None = None
    location_name: str | None = None


class DraftBrief(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    draft_text: str
    legal_references: list
    confidence_score: float
    status: str
    generation_model: str | None = None
    generation_time_ms: int | None = None
    created_at: datetime


class AppealDetail(AppealBrief):
    text: str
    district: str | None = None
    external_id: str | None = None
    source_external_ref: str | None = None
    department_id: int | None = None
    risk_reasons: list
    escalation_level: str | None = None
    escalation_reason: str | None = None
    escalated_at: datetime | None = None
    campaign_score: float
    campaign_cluster_id: int | None = None
    duplicate_of_id: int | None = None
    duplicate_score: float
    tags: list[str] | None = None
    analyzed_at: datetime | None = None
    resolved_at: datetime | None = None
    created_at: datetime
    draft_response: DraftBrief | None = None
    attachments: list[AttachmentOut] = []


class MyAppealBrief(BaseModel):
    """Карточка обращения для заявителя — без внутренних AI-оценок."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    category: str
    subcategory: str | None = None
    region: str
    status: str
    submitted_at: datetime
    resolved_at: datetime | None = None


class MyAppealDetail(MyAppealBrief):
    text: str
    district: str | None = None
    latitude: float | None = None
    longitude: float | None = None
    location_name: str | None = None
    attachments: list[AttachmentOut] = []
    events: list[AppealEventOut] = []
    # Официальный ответ — только после утверждения
    official_response: str | None = None
    response_status: str | None = None
    expected_response_time: str | None = None
    responsible_department: str | None = None


class PaginatedAppeals(BaseModel):
    items: list[AppealBrief]
    total: int
    page: int
    page_size: int


class PaginatedMyAppeals(BaseModel):
    items: list[MyAppealBrief]
    total: int
    page: int
    page_size: int
