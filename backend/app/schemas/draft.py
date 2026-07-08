from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.schemas.appeal import AppealBrief


class DraftUpdate(BaseModel):
    draft_text: str


class DraftOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    appeal_id: int
    draft_text: str
    legal_references: list
    confidence_score: float
    status: str
    reviewed_by_id: int | None = None
    reviewed_at: datetime | None = None
    generation_model: str | None = None
    generation_time_ms: int | None = None
    created_at: datetime
    appeal: AppealBrief | None = None


class PaginatedDrafts(BaseModel):
    items: list[DraftOut]
    total: int
    page: int
    page_size: int
