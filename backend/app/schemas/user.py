from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class RegisterRequest(BaseModel):
    """Самостоятельная регистрация пользователя портала (роль requester)."""

    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    full_name: str = Field(min_length=3, max_length=200)
    requester_type: str = "patient"  # patient, relative, medical_worker, guardian, external
    affiliation: str | None = None  # регион / организация


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    email: str
    full_name: str
    role: str
    position: str | None = None
    department_id: int | None = None
    requester_id: int | None = None
    is_active: bool
    last_login_at: datetime | None = None


class UserAdminUpdate(BaseModel):
    role: str | None = None
    is_active: bool | None = None
    department_id: int | None = None
    position: str | None = None


class LoginResponse(BaseModel):
    user: UserOut
    token_type: str = "cookie"
