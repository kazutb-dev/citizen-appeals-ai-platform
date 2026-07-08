import hashlib
from datetime import datetime

from fastapi import APIRouter, Depends, Request, Response
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.audit import record_audit
from app.core.auth import (
    REFRESH_COOKIE,
    clear_auth_cookies,
    decode_token,
    get_current_user,
    hash_password,
    set_auth_cookies,
    verify_password,
)
from app.core.exceptions import AuthError, ConflictError
from app.data.categories import REQUESTER_TYPES
from app.database import get_db
from app.models.requester import Requester
from app.models.user import User
from app.schemas.user import (
    LoginRequest,
    LoginResponse,
    RegisterRequest,
    UserLanguageUpdate,
    UserOut,
)

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=LoginResponse, status_code=201)
async def register(
    payload: RegisterRequest, response: Response, db: AsyncSession = Depends(get_db)
) -> LoginResponse:
    """Самостоятельная регистрация пользователя портала (роль requester)."""
    if payload.requester_type not in REQUESTER_TYPES:
        raise ConflictError(f"Недопустимый тип заявителя: {payload.requester_type}")
    existing = (
        await db.execute(select(User).where(User.email == payload.email))
    ).scalar_one_or_none()
    if existing is not None:
        raise ConflictError("Пользователь с таким email уже зарегистрирован")

    identifier_hash = hashlib.sha256(payload.email.strip().lower().encode()).hexdigest()
    requester = (
        await db.execute(
            select(Requester).where(Requester.identifier_hash == identifier_hash)
        )
    ).scalar_one_or_none()
    if requester is None:
        requester = Requester(
            identifier_hash=identifier_hash,
            email_hash=identifier_hash,
            full_name=payload.full_name,
            requester_type=payload.requester_type,
            affiliation=payload.affiliation,
        )
        db.add(requester)
        await db.flush()

    user = User(
        email=payload.email,
        hashed_password=hash_password(payload.password),
        full_name=payload.full_name,
        role="requester",
        requester_id=requester.id,
        position=REQUESTER_TYPES[payload.requester_type],
    )
    db.add(user)
    await db.flush()
    await record_audit(
        db, action="user_registered", entity_type="user", entity_id=user.id,
        user_id=user.id, actor=user.email,
        details={"requester_type": payload.requester_type, "affiliation": payload.affiliation},
    )
    await db.commit()

    set_auth_cookies(response, user.id)
    return LoginResponse(user=UserOut.model_validate(user))


@router.post("/login", response_model=LoginResponse)
async def login(
    payload: LoginRequest, response: Response, db: AsyncSession = Depends(get_db)
) -> LoginResponse:
    user = (
        await db.execute(select(User).where(User.email == payload.email))
    ).scalar_one_or_none()
    if user is None or not verify_password(payload.password, user.hashed_password):
        raise AuthError("Неверный email или пароль")
    if not user.is_active:
        raise AuthError("Учётная запись деактивирована")

    user.last_login_at = datetime.utcnow()
    await record_audit(
        db, action="login", entity_type="user", entity_id=user.id,
        user_id=user.id, actor=user.email,
    )
    await db.commit()

    set_auth_cookies(response, user.id)
    return LoginResponse(user=UserOut.model_validate(user))


@router.post("/refresh", response_model=LoginResponse)
async def refresh(
    request: Request, response: Response, db: AsyncSession = Depends(get_db)
) -> LoginResponse:
    token = request.cookies.get(REFRESH_COOKIE)
    if not token:
        raise AuthError("Refresh-токен отсутствует")
    user_id = decode_token(token, "refresh")
    user = (await db.execute(select(User).where(User.id == user_id))).scalar_one_or_none()
    if user is None or not user.is_active:
        raise AuthError("Пользователь не найден или деактивирован")
    set_auth_cookies(response, user.id)
    return LoginResponse(user=UserOut.model_validate(user))


@router.get("/me", response_model=UserOut)
async def me(user: User = Depends(get_current_user)) -> UserOut:
    return UserOut.model_validate(user)


@router.patch("/me/language", response_model=UserOut)
async def update_my_language(
    payload: UserLanguageUpdate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> UserOut:
    lang = payload.preferred_language.strip().lower().replace("_", "-")[:2]
    if lang not in {"kk", "ru", "en"}:
        raise ConflictError("Недопустимый язык интерфейса")
    user.preferred_language = lang
    await db.commit()
    await db.refresh(user)
    return UserOut.model_validate(user)


@router.post("/logout")
async def logout(
    response: Response,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    await record_audit(
        db, action="logout", entity_type="user", entity_id=user.id,
        user_id=user.id, actor=user.email,
    )
    await db.commit()
    clear_auth_cookies(response)
    return {"detail": "Выход выполнен"}
