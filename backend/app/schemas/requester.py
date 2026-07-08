from datetime import datetime

from pydantic import BaseModel, ConfigDict


class RequesterBrief(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    full_name: str
    requester_type: str
    affiliation: str | None = None
    region: str | None = None
    category: str
    is_repeat_complainant: bool


class RequesterOut(RequesterBrief):
    total_appeals: int
    resolved_appeals: int
    rejected_appeals: int
    first_appeal_date: datetime | None = None
    last_appeal_date: datetime | None = None
    category_score: float
    repeat_score: float
    top_topics: list
    top_regions: list
    behavior_stats: dict
    created_at: datetime


class PaginatedRequesters(BaseModel):
    items: list[RequesterOut]
    total: int
    page: int
    page_size: int
