from datetime import datetime

from pydantic import BaseModel, ConfigDict


class NotificationOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    appeal_id: int | None = None
    type: str
    title: str
    body: str | None = None
    is_read: bool
    created_at: datetime


class PaginatedNotifications(BaseModel):
    items: list[NotificationOut]
    total: int
    unread: int
    page: int
    page_size: int
