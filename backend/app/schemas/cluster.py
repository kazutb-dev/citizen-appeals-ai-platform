from datetime import datetime

from pydantic import BaseModel, ConfigDict


class ClusterOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    description: str | None = None
    cluster_type: str
    topic: str
    category: str
    appeal_count: int
    requester_count: int
    region_spread: dict
    growth_rate: float
    peak_rate_per_hour: float
    is_trending: bool
    trend_score: float
    coordination_score: float
    similarity_score: float
    status: str
    first_seen: datetime | None = None
    last_updated: datetime
