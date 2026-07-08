"""События обращений и уведомления пользователей — единая точка записи."""
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.appeal import Appeal, AppealEvent
from app.models.notification import Notification
from app.models.user import User


async def add_appeal_event(
    db: AsyncSession,
    appeal_id: int,
    event_type: str,
    *,
    actor: str = "system",
    comment: str | None = None,
    details: dict | None = None,
    is_public: bool = True,
) -> AppealEvent:
    event = AppealEvent(
        appeal_id=appeal_id,
        event_type=event_type,
        actor=actor,
        comment=comment,
        details=details or {},
        is_public=is_public,
    )
    db.add(event)
    await db.flush()
    return event


async def notify_requester(
    db: AsyncSession,
    appeal: Appeal,
    *,
    type: str,
    title: str,
    body: str | None = None,
) -> None:
    """Уведомление пользователю портала, связанному с заявителем обращения."""
    if appeal.requester_id is None:
        return
    portal_user = (
        await db.execute(select(User).where(User.requester_id == appeal.requester_id))
    ).scalar_one_or_none()
    if portal_user is None:
        return
    db.add(
        Notification(
            user_id=portal_user.id,
            appeal_id=appeal.id,
            type=type,
            title=title,
            body=body,
        )
    )
    await db.flush()
