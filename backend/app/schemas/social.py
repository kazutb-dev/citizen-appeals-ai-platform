from datetime import datetime

from pydantic import BaseModel, ConfigDict


class SocialPostOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    platform: str
    source_id: int | None = None
    source_account: str
    source_name: str
    post_url: str | None = None
    post_text: str
    post_date: datetime
    views: int
    likes: int
    comments: int
    shares: int
    topic: str | None = None
    category: str | None = None
    region: str | None = None
    risk_level: str
    sentiment: str
    tags: list[str] | None = None
    is_converted_to_appeal: bool
    linked_appeal_id: int | None = None


class PaginatedSocialPosts(BaseModel):
    items: list[SocialPostOut]
    total: int
    page: int
    page_size: int


class TrendingTopic(BaseModel):
    topic: str
    category: str | None = None
    post_count: int
    total_views: int
    max_risk_level: str


# === Социальная аналитика ===


class SentimentPoint(BaseModel):
    date: str
    positive: int
    neutral: int
    negative: int
    alarming: int


class TopicTrend(BaseModel):
    topic: str
    current_count: int
    previous_count: int
    growth_pct: float
    dominant_sentiment: str


class SpikePoint(BaseModel):
    date: str
    count: int
    expected: float
    deviation: float  # во сколько раз выше ожидаемого


class SourceActivity(BaseModel):
    source_name: str
    platform: str
    post_count: int
    total_views: int
    negative_share: float


class ReputationPoint(BaseModel):
    date: str
    score: float  # (positive - negative - 2*alarming) / total, от -1 до 1
    post_count: int


class DepartmentImpact(BaseModel):
    category: str
    department: str | None = None
    post_count: int
    negative_count: int
    total_views: int
