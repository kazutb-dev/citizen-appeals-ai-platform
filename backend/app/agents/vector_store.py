"""Поиск похожих обращений через pgvector (косинусное сходство)."""
from dataclasses import dataclass
from datetime import datetime, timedelta

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.appeal import Appeal


@dataclass
class SimilarAppeal:
    appeal: Appeal
    similarity: float

    @property
    def id(self) -> int:
        return self.appeal.id

    @property
    def text(self) -> str:
        return self.appeal.text

    @property
    def region(self) -> str:
        return self.appeal.region

    @property
    def submitted_at(self) -> datetime:
        return self.appeal.submitted_at


async def find_similar(
    db: AsyncSession,
    embedding: list[float],
    *,
    threshold: float,
    exclude_id: int | None = None,
    requester_id: int | None = None,
    time_window_hours: int | None = None,
    time_window_days: int | None = None,
    limit: int = 50,
) -> list[SimilarAppeal]:
    """Возвращает обращения со сходством >= threshold, отсортированные по убыванию."""
    distance = Appeal.embedding.cosine_distance(embedding)
    similarity = (1 - distance).label("similarity")

    stmt = (
        select(Appeal, similarity)
        .where(Appeal.embedding.is_not(None))
        .where(similarity >= threshold)
        .order_by(distance)
        .limit(limit)
    )
    if exclude_id is not None:
        stmt = stmt.where(Appeal.id != exclude_id)
    if requester_id is not None:
        stmt = stmt.where(Appeal.requester_id == requester_id)

    cutoff: datetime | None = None
    if time_window_hours is not None:
        cutoff = datetime.utcnow() - timedelta(hours=time_window_hours)
    elif time_window_days is not None:
        cutoff = datetime.utcnow() - timedelta(days=time_window_days)
    if cutoff is not None:
        stmt = stmt.where(Appeal.submitted_at >= cutoff)

    rows = (await db.execute(stmt)).all()
    return [SimilarAppeal(appeal=row[0], similarity=float(row[1])) for row in rows]
