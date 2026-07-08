"""Справочники для форм: категории, регионы, типы заявителей."""
from fastapi import APIRouter, Depends

from app.core.permissions import Role, require_role
from app.data.categories import CATEGORY_GROUPS, REQUESTER_TYPES
from app.data.departments_data import (
    REGIONS,
    ORG_NAME_EN,
    ORG_NAME_KZ,
    ORG_NAME_RU,
)
from app.models.user import User

router = APIRouter(prefix="/meta", tags=["meta"])


@router.get("/categories")
async def categories(user: User = Depends(require_role(Role.REQUESTER))) -> dict:
    return CATEGORY_GROUPS


@router.get("/locations")
async def locations(user: User = Depends(require_role(Role.REQUESTER))) -> list[str]:
    return REGIONS


@router.get("/requester-types")
async def requester_types(user: User = Depends(require_role(Role.REQUESTER))) -> dict:
    return REQUESTER_TYPES


@router.get("/organization")
async def organization() -> dict:
    """Название организации — публично (нужно на странице входа)."""
    return {
        "ru": ORG_NAME_RU,
        "kz": ORG_NAME_KZ,
        "en": ORG_NAME_EN,
    }
