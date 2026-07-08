"""Журнал аудита: единая точка записи значимых действий."""
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.audit import AuditLog


async def record_audit(
    db: AsyncSession,
    *,
    action: str,
    entity_type: str,
    entity_id: int | None = None,
    user_id: int | None = None,
    actor: str = "system",
    details: dict | None = None,
) -> None:
    db.add(
        AuditLog(
            user_id=user_id,
            actor=actor,
            action=action,
            entity_type=entity_type,
            entity_id=entity_id,
            details=details or {},
        )
    )
    await db.flush()
