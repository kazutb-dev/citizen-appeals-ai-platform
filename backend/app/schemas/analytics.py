from datetime import datetime

from pydantic import BaseModel, ConfigDict


class OverviewKpi(BaseModel):
    appeals_today: int
    appeals_today_trend_pct: float
    critical_open: int
    campaigns_detected: int
    ai_processed: int
    ai_processed_pct: float
    avg_response_days: float
    total_appeals: int


class TrendPoint(BaseModel):
    date: str
    count: int
    critical: int


class RegionStat(BaseModel):
    region: str
    total: int
    critical: int
    escalated: int
    campaigns: int


class CategoryStat(BaseModel):
    category: str
    count: int


class AgentStat(BaseModel):
    agent: str
    name: str
    processed: int
    flagged: int


class AuditLogOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int | None = None
    actor: str
    action: str
    entity_type: str
    entity_id: int | None = None
    details: dict
    created_at: datetime


class PaginatedAudit(BaseModel):
    items: list[AuditLogOut]
    total: int
    page: int
    page_size: int
