"""Начальная схема AGRP: граждане, обращения, кластеры, проекты ответов,
посты соцсетей, пользователи, министерства, журнал аудита. pgvector 1024 dim.

Revision ID: 001
Revises:
Create Date: 2026-06-10
"""
import sqlalchemy as sa
from alembic import op
from pgvector.sqlalchemy import Vector
from sqlalchemy.dialects.postgresql import ARRAY

revision = "001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")

    op.create_table(
        "ministries",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(300), nullable=False, unique=True),
        sa.Column("short_name", sa.String(100)),
        sa.Column("code", sa.String(30), unique=True),
        sa.Column("categories", ARRAY(sa.String()), server_default="{}"),
        sa.Column("contact_email", sa.String(255)),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("now()")),
    )

    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("email", sa.String(255), nullable=False, unique=True, index=True),
        sa.Column("hashed_password", sa.String(255), nullable=False),
        sa.Column("full_name", sa.String(200), nullable=False),
        sa.Column("role", sa.String(30), nullable=False, server_default="viewer"),
        sa.Column("ministry_id", sa.Integer(), sa.ForeignKey("ministries.id")),
        sa.Column("position", sa.String(200)),
        sa.Column("is_active", sa.Boolean(), server_default=sa.text("true")),
        sa.Column("last_login_at", sa.DateTime()),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.text("now()")),
    )

    op.create_table(
        "citizens",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("iin_hash", sa.String(64), nullable=False, unique=True, index=True),
        sa.Column("full_name", sa.String(200), nullable=False),
        sa.Column("phone_hash", sa.String(64)),
        sa.Column("email_hash", sa.String(64)),
        sa.Column("region", sa.String(100)),
        sa.Column("total_appeals", sa.Integer(), server_default="0"),
        sa.Column("resolved_appeals", sa.Integer(), server_default="0"),
        sa.Column("rejected_appeals", sa.Integer(), server_default="0"),
        sa.Column("first_appeal_date", sa.DateTime()),
        sa.Column("last_appeal_date", sa.DateTime()),
        sa.Column("category", sa.String(50), server_default="normal"),
        sa.Column("category_score", sa.Float(), server_default="0"),
        sa.Column("category_updated_at", sa.DateTime()),
        sa.Column("is_querulant", sa.Boolean(), server_default=sa.text("false")),
        sa.Column("querulant_score", sa.Float(), server_default="0"),
        sa.Column("top_topics", sa.JSON(), server_default="[]"),
        sa.Column("top_regions", sa.JSON(), server_default="[]"),
        sa.Column("behavior_stats", sa.JSON(), server_default="{}"),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.text("now()")),
    )

    op.create_table(
        "appeal_clusters",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(300), nullable=False),
        sa.Column("description", sa.Text()),
        sa.Column("cluster_type", sa.String(50), nullable=False),
        sa.Column("topic", sa.String(200), nullable=False),
        sa.Column("category", sa.String(50), nullable=False),
        sa.Column("appeal_count", sa.Integer(), server_default="0"),
        sa.Column("citizen_count", sa.Integer(), server_default="0"),
        sa.Column("region_spread", sa.JSON(), server_default="{}"),
        sa.Column("growth_rate", sa.Float(), server_default="0"),
        sa.Column("peak_rate_per_hour", sa.Float(), server_default="0"),
        sa.Column("is_trending", sa.Boolean(), server_default=sa.text("false")),
        sa.Column("trend_score", sa.Float(), server_default="0"),
        sa.Column("coordination_score", sa.Float(), server_default="0"),
        sa.Column("similarity_score", sa.Float(), server_default="0"),
        sa.Column("status", sa.String(50), server_default="active"),
        sa.Column("first_seen", sa.DateTime()),
        sa.Column("last_updated", sa.DateTime(), server_default=sa.text("now()")),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("now()")),
    )

    op.create_table(
        "appeals",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "citizen_id", sa.Integer(), sa.ForeignKey("citizens.id"), nullable=False, index=True
        ),
        sa.Column("ministry_id", sa.Integer(), sa.ForeignKey("ministries.id")),
        sa.Column("external_id", sa.String(100), unique=True),
        sa.Column("title", sa.String(500), nullable=False),
        sa.Column("text", sa.Text(), nullable=False),
        sa.Column("category", sa.String(50), nullable=False, index=True),
        sa.Column("subcategory", sa.String(100)),
        sa.Column("region", sa.String(100), nullable=False, index=True),
        sa.Column("district", sa.String(100)),
        sa.Column("status", sa.String(50), server_default="new", index=True),
        sa.Column("risk_level", sa.String(20), server_default="low", index=True),
        sa.Column("risk_score", sa.Float(), server_default="0"),
        sa.Column("risk_reasons", sa.JSON(), server_default="[]"),
        sa.Column("is_escalated", sa.Boolean(), server_default=sa.text("false")),
        sa.Column("escalation_level", sa.String(20)),
        sa.Column("escalation_reason", sa.Text()),
        sa.Column("escalated_at", sa.DateTime()),
        sa.Column("is_infodrop", sa.Boolean(), server_default=sa.text("false")),
        sa.Column("infodrop_score", sa.Float(), server_default="0"),
        sa.Column("infodrop_cluster_id", sa.Integer(), sa.ForeignKey("appeal_clusters.id")),
        sa.Column("is_duplicate", sa.Boolean(), server_default=sa.text("false")),
        sa.Column("duplicate_of_id", sa.Integer(), sa.ForeignKey("appeals.id")),
        sa.Column("duplicate_score", sa.Float(), server_default="0"),
        sa.Column("from_querulant", sa.Boolean(), server_default=sa.text("false")),
        sa.Column("tags", ARRAY(sa.String()), server_default="{}"),
        sa.Column("embedding", Vector(1024)),
        sa.Column("submitted_at", sa.DateTime(), server_default=sa.text("now()"), index=True),
        sa.Column("analyzed_at", sa.DateTime()),
        sa.Column("resolved_at", sa.DateTime()),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.text("now()")),
    )
    # HNSW-индекс для быстрого косинусного поиска похожих обращений
    op.execute(
        "CREATE INDEX ix_appeals_embedding_hnsw ON appeals "
        "USING hnsw (embedding vector_cosine_ops)"
    )

    op.create_table(
        "cluster_memberships",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "cluster_id", sa.Integer(), sa.ForeignKey("appeal_clusters.id"), nullable=False
        ),
        sa.Column("appeal_id", sa.Integer(), sa.ForeignKey("appeals.id"), nullable=False),
        sa.Column("similarity_score", sa.Float(), server_default="0"),
        sa.Column("added_at", sa.DateTime(), server_default=sa.text("now()")),
        sa.UniqueConstraint("cluster_id", "appeal_id", name="uq_cluster_appeal"),
    )

    op.create_table(
        "draft_responses",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "appeal_id", sa.Integer(), sa.ForeignKey("appeals.id"), unique=True, nullable=False
        ),
        sa.Column("draft_text", sa.Text(), nullable=False),
        sa.Column("legal_references", sa.JSON(), server_default="[]"),
        sa.Column("confidence_score", sa.Float(), server_default="0"),
        sa.Column("status", sa.String(30), server_default="draft"),
        sa.Column("reviewed_by_id", sa.Integer(), sa.ForeignKey("users.id")),
        sa.Column("reviewed_at", sa.DateTime()),
        sa.Column("generation_model", sa.String(100)),
        sa.Column("generation_time_ms", sa.Integer()),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.text("now()")),
    )

    op.create_table(
        "social_posts",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("platform", sa.String(30), nullable=False, index=True),
        sa.Column("source_account", sa.String(200), nullable=False),
        sa.Column("source_name", sa.String(300), nullable=False),
        sa.Column("post_url", sa.String(500)),
        sa.Column("post_text", sa.Text(), nullable=False),
        sa.Column("post_date", sa.DateTime(), nullable=False, index=True),
        sa.Column("views", sa.Integer(), server_default="0"),
        sa.Column("likes", sa.Integer(), server_default="0"),
        sa.Column("comments", sa.Integer(), server_default="0"),
        sa.Column("shares", sa.Integer(), server_default="0"),
        sa.Column("topic", sa.String(200)),
        sa.Column("category", sa.String(50)),
        sa.Column("region", sa.String(100)),
        sa.Column("risk_level", sa.String(20), server_default="low"),
        sa.Column("sentiment", sa.String(20), server_default="neutral"),
        sa.Column("tags", ARRAY(sa.String()), server_default="{}"),
        sa.Column("is_converted_to_appeal", sa.Boolean(), server_default=sa.text("false")),
        sa.Column("linked_appeal_id", sa.Integer(), sa.ForeignKey("appeals.id")),
        sa.Column("embedding", Vector(1024)),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("now()")),
    )

    op.create_table(
        "audit_logs",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), index=True),
        sa.Column("actor", sa.String(100), nullable=False, server_default="system"),
        sa.Column("action", sa.String(100), nullable=False, index=True),
        sa.Column("entity_type", sa.String(50), nullable=False),
        sa.Column("entity_id", sa.Integer(), index=True),
        sa.Column("details", sa.JSON(), server_default="{}"),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("now()"), index=True),
    )


def downgrade() -> None:
    op.drop_table("audit_logs")
    op.drop_table("social_posts")
    op.drop_table("draft_responses")
    op.drop_table("cluster_memberships")
    op.drop_table("appeals")
    op.drop_table("appeal_clusters")
    op.drop_table("citizens")
    op.drop_table("users")
    op.drop_table("ministries")
    op.execute("DROP EXTENSION IF EXISTS vector")
