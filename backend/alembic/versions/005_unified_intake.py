"""Единый учёт обращений (Phase 1): канал-источник и геолокация.

Аддитивная, неразрушающая миграция. Новые nullable-колонки на appeals:
- source_channel      — канал поступления обращения (portal, ikomek, crm, eotinish,
                        damumed, telegram, instagram, other);
- source_external_ref — идентификатор обращения в системе-источнике (для дедупликации
                        между каналами и обратной связи с внешней системой);
- latitude / longitude — координаты места возникновения проблемы (обязательны для новых
                        обращений портала — «без координат обращение отправить нельзя»);
- location_name       — человекочитаемый адрес/название места;
- intake_hash         — хэш идемпотентности приёма (защита от точных дублей между каналами).

Существующие обращения получают source_channel='portal' (известное значение).

Revision ID: 005
Revises: 004
"""
import sqlalchemy as sa
from alembic import op

revision = "005"
down_revision = "004"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("appeals", sa.Column("source_channel", sa.String(30), nullable=True))
    op.add_column("appeals", sa.Column("source_external_ref", sa.String(200), nullable=True))
    op.add_column("appeals", sa.Column("latitude", sa.Float(), nullable=True))
    op.add_column("appeals", sa.Column("longitude", sa.Float(), nullable=True))
    op.add_column("appeals", sa.Column("location_name", sa.String(300), nullable=True))
    op.add_column("appeals", sa.Column("intake_hash", sa.String(64), nullable=True))
    op.create_index("ix_appeals_source_channel", "appeals", ["source_channel"])
    op.create_index("ix_appeals_intake_hash", "appeals", ["intake_hash"])
    # Backfill: все ранее созданные обращения поступили через портал.
    op.execute("UPDATE appeals SET source_channel = 'portal' WHERE source_channel IS NULL")


def downgrade() -> None:
    op.drop_index("ix_appeals_intake_hash", table_name="appeals")
    op.drop_index("ix_appeals_source_channel", table_name="appeals")
    op.drop_column("appeals", "intake_hash")
    op.drop_column("appeals", "location_name")
    op.drop_column("appeals", "longitude")
    op.drop_column("appeals", "latitude")
    op.drop_column("appeals", "source_external_ref")
    op.drop_column("appeals", "source_channel")
