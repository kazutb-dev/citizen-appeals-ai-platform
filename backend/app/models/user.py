from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String

from app.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(200), nullable=False)

    role = Column(String(30), nullable=False, default="requester")
    # admin, analyst, operator, viewer, requester (пользователь портала)

    department_id = Column(Integer, ForeignKey("departments.id"), nullable=True)
    requester_id = Column(Integer, ForeignKey("requesters.id"), nullable=True)
    # профиль заявителя для пользователей портала (пациенты, родственники, медработники)
    tenant_id = Column(Integer, ForeignKey("tenants.id"), nullable=True, index=True)
    position = Column(String(200), nullable=True)
    preferred_language = Column(String(5), nullable=True, default="ru")

    is_active = Column(Boolean, default=True)
    last_login_at = Column(DateTime, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
