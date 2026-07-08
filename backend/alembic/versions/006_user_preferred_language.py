"""Профиль пользователя: сохраняемый язык интерфейса.

Аддитивная миграция: добавляет nullable-колонку preferred_language в users,
без влияния на текущую авторизацию и RBAC.

Revision ID: 006
Revises: 005
"""
import sqlalchemy as sa
from alembic import op

revision = "006"
down_revision = "005"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("users", sa.Column("preferred_language", sa.String(length=5), nullable=True))
    op.execute("UPDATE users SET preferred_language = 'ru' WHERE preferred_language IS NULL")


def downgrade() -> None:
    op.drop_column("users", "preferred_language")
