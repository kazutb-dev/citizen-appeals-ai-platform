"""RBAC: роли и фабрика зависимостей для проверки прав."""
from enum import StrEnum

from fastapi import Depends

from app.core.auth import get_current_user
from app.core.exceptions import ForbiddenError
from app.models.user import User


class Role(StrEnum):
    ADMIN = "admin"
    ANALYST = "analyst"
    OPERATOR = "operator"
    VIEWER = "viewer"
    REQUESTER = "requester"  # пользователь портала: пациент, родственник, медработник


# Иерархия: каждая роль включает права всех ролей ниже.
# requester — самый низкий уровень: видит только свои обращения.
ROLE_HIERARCHY: dict[str, int] = {
    Role.REQUESTER: 0,
    Role.VIEWER: 1,
    Role.OPERATOR: 2,
    Role.ANALYST: 3,
    Role.ADMIN: 4,
}


def require_role(minimum: Role):
    """Зависимость FastAPI: пользователь должен иметь роль не ниже minimum."""

    async def checker(user: User = Depends(get_current_user)) -> User:
        if ROLE_HIERARCHY.get(user.role, -1) < ROLE_HIERARCHY[minimum]:
            raise ForbiddenError(f"Требуется роль не ниже «{minimum}»")
        return user

    return checker
