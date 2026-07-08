"""Оргструктура медорганизации: иерархия и SLA подразделений.

Добавляет departments.parent_code (иерархия оргструктуры) и
departments.response_sla_hours (целевой срок ответа). Аддитивная,
неразрушающая миграция.

Revision ID: 003
Revises: 002
"""
import sqlalchemy as sa
from alembic import op

revision = "003"
down_revision = "002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("departments", sa.Column("parent_code", sa.String(30), nullable=True))
    op.add_column("departments", sa.Column("response_sla_hours", sa.Integer(), nullable=True))
    op.create_index("ix_departments_parent_code", "departments", ["parent_code"])


def downgrade() -> None:
    op.drop_index("ix_departments_parent_code", table_name="departments")
    op.drop_column("departments", "response_sla_hours")
    op.drop_column("departments", "parent_code")
