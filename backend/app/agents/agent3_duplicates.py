"""Агент 3: обнаружение дубликатов по семантическому сходству."""
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.agents import agent_config, vector_store
from app.models.appeal import Appeal

DUPLICATE_CONFIG = {
    "same_requester_threshold": 0.88,  # порог для дубликата от того же заявителя
    "any_requester_threshold": 0.93,   # порог для дубликата от любого заявителя
    "time_window_days_same": 90,       # окно для одного заявителя
    "time_window_days_any": 30,        # окно для всех заявителей
}


class DuplicateResult(BaseModel):
    is_duplicate: bool = False
    duplicate_of_id: int | None = None
    score: float = 0.0
    reason: str = ""


async def analyze(appeal: Appeal, db: AsyncSession) -> DuplicateResult:
    if appeal.embedding is None:
        return DuplicateResult()

    config = await agent_config.get_config(db, "agent3", DUPLICATE_CONFIG)
    embedding = list(appeal.embedding)

    # 1. Поиск дубликатов от того же заявителя
    if appeal.requester_id is not None:
        same_requester_results = await vector_store.find_similar(
            db,
            embedding,
            threshold=config["same_requester_threshold"],
            time_window_days=config["time_window_days_same"],
            requester_id=appeal.requester_id,
            exclude_id=appeal.id,
        )
        if same_requester_results:
            best_match = same_requester_results[0]
            return DuplicateResult(
                is_duplicate=True,
                duplicate_of_id=best_match.id,
                score=best_match.similarity,
                reason=f"Повторное обращение от этого же заявителя (#{best_match.id})",
            )

    # 2. Поиск дубликатов от всех заявителей (более строгий порог)
    any_requester_results = await vector_store.find_similar(
        db,
        embedding,
        threshold=config["any_requester_threshold"],
        time_window_days=config["time_window_days_any"],
        exclude_id=appeal.id,
    )
    if any_requester_results:
        best_match = any_requester_results[0]
        return DuplicateResult(
            is_duplicate=True,
            duplicate_of_id=best_match.id,
            score=best_match.similarity,
            reason=f"Практически идентичное обращение уже существует (#{best_match.id})",
        )

    return DuplicateResult()
