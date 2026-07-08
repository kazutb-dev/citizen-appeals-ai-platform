"""Миграция схемы данных (002): переход к модели обращений здравоохранения.

Переименования без потери данных: citizens→requesters, ministries→departments,
колонки citizen_id→requester_id, ministry_id→department_id,
is_infodrop→is_campaign, querulant→repeat_complainant.

Новые таблицы: social_sources, integrations, appeal_attachments, appeal_events,
notifications, knowledge_documents, knowledge_chunks (pgvector), agent_settings.

Revision ID: 002
Revises: 001
Create Date: 2026-06-11
"""
import sqlalchemy as sa
from alembic import op
from pgvector.sqlalchemy import Vector

revision = "002"
down_revision = "001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # === Переименования (данные сохраняются) ===
    op.rename_table("citizens", "requesters")
    op.alter_column("requesters", "iin_hash", new_column_name="identifier_hash")
    op.alter_column("requesters", "is_querulant", new_column_name="is_repeat_complainant")
    op.alter_column("requesters", "querulant_score", new_column_name="repeat_score")
    op.add_column(
        "requesters",
        sa.Column("requester_type", sa.String(30), nullable=False, server_default="student"),
    )
    # факультет / кафедра / программа / подразделение
    op.add_column("requesters", sa.Column("affiliation", sa.String(200)))

    op.rename_table("ministries", "departments")
    op.add_column(
        "departments",
        sa.Column("department_type", sa.String(50), server_default="administration"),
    )
    # dean_office, student_affairs, academic_affairs, registrar,
    # finance, it, hr, dormitory, administration

    op.alter_column("appeals", "citizen_id", new_column_name="requester_id")
    op.alter_column("appeals", "ministry_id", new_column_name="department_id")
    op.alter_column("appeals", "is_infodrop", new_column_name="is_campaign")
    op.alter_column("appeals", "infodrop_score", new_column_name="campaign_score")
    op.alter_column("appeals", "infodrop_cluster_id", new_column_name="campaign_cluster_id")
    op.alter_column("appeals", "from_querulant", new_column_name="from_repeat_complainant")

    op.alter_column("users", "ministry_id", new_column_name="department_id")
    op.add_column(
        "users", sa.Column("requester_id", sa.Integer(), sa.ForeignKey("requesters.id"))
    )

    op.alter_column("appeal_clusters", "citizen_count", new_column_name="requester_count")

    # === Источники социальных сетей (Администрирование → Социальные источники) ===
    op.create_table(
        "social_sources",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("platform", sa.String(30), nullable=False, index=True),
        # instagram, telegram, facebook, tiktok, youtube, vk, x
        sa.Column("url", sa.String(500)),
        sa.Column("credentials", sa.JSON(), server_default="{}"),
        sa.Column("polling_interval_minutes", sa.Integer(), server_default="30"),
        sa.Column("is_enabled", sa.Boolean(), server_default=sa.text("true")),
        sa.Column("last_polled_at", sa.DateTime()),
        sa.Column("last_status", sa.String(50), server_default="pending"),
        # pending, ok, error, not_configured
        sa.Column("last_error", sa.Text()),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.text("now()")),
    )
    op.add_column(
        "social_posts",
        sa.Column("source_id", sa.Integer(), sa.ForeignKey("social_sources.id")),
    )

    # === Интеграции (Instagram Graph API и др.) ===
    op.create_table(
        "integrations",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("provider", sa.String(50), nullable=False, unique=True),
        sa.Column("config", sa.JSON(), server_default="{}"),
        # app_id, business_account_id, redirect_uri, oauth_state, ...
        sa.Column("secrets", sa.JSON(), server_default="{}"),
        # app_secret, access_token, refresh_token — отдаются только маской
        sa.Column("status", sa.String(30), server_default="not_configured"),
        # not_configured, configured, connected, error
        sa.Column("token_expires_at", sa.DateTime()),
        sa.Column("last_health_check_at", sa.DateTime()),
        sa.Column("last_health_status", sa.String(300)),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.text("now()")),
    )

    # === Вложения к обращениям ===
    op.create_table(
        "appeal_attachments",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "appeal_id", sa.Integer(), sa.ForeignKey("appeals.id"), nullable=False, index=True
        ),
        sa.Column("filename", sa.String(300), nullable=False),
        sa.Column("content_type", sa.String(100)),
        sa.Column("size_bytes", sa.Integer(), server_default="0"),
        sa.Column("storage_path", sa.String(500), nullable=False),
        sa.Column("uploaded_by_id", sa.Integer(), sa.ForeignKey("users.id")),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("now()")),
    )

    # === История обращения (видимая заявителю лента событий) ===
    op.create_table(
        "appeal_events",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "appeal_id", sa.Integer(), sa.ForeignKey("appeals.id"), nullable=False, index=True
        ),
        sa.Column("event_type", sa.String(50), nullable=False),
        # submitted, analysis_started, analysis_done, assigned, status_changed,
        # response_drafted, response_approved, response_sent, escalated, comment
        sa.Column("actor", sa.String(100), server_default="system"),
        sa.Column("comment", sa.Text()),
        sa.Column("details", sa.JSON(), server_default="{}"),
        sa.Column("is_public", sa.Boolean(), server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("now()"), index=True),
    )

    # === Уведомления пользователей ===
    op.create_table(
        "notifications",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False, index=True
        ),
        sa.Column("appeal_id", sa.Integer(), sa.ForeignKey("appeals.id")),
        sa.Column("type", sa.String(50), nullable=False),
        # appeal_status, appeal_response, appeal_escalated, system
        sa.Column("title", sa.String(300), nullable=False),
        sa.Column("body", sa.Text()),
        sa.Column("is_read", sa.Boolean(), server_default=sa.text("false"), index=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("now()"), index=True),
    )

    # === База знаний (RAG для Агента 4) ===
    op.create_table(
        "knowledge_documents",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("title", sa.String(300), nullable=False),
        sa.Column("doc_type", sa.String(50), server_default="regulation"),
        # regulation, policy, academic_rule, handbook, hr_policy, procedure
        sa.Column("department_id", sa.Integer(), sa.ForeignKey("departments.id")),
        sa.Column("filename", sa.String(300)),
        sa.Column("storage_path", sa.String(500)),
        sa.Column("status", sa.String(30), server_default="processing"),
        # processing, ready, failed
        sa.Column("error", sa.Text()),
        sa.Column("chunk_count", sa.Integer(), server_default="0"),
        sa.Column("uploaded_by_id", sa.Integer(), sa.ForeignKey("users.id")),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.text("now()")),
    )
    op.create_table(
        "knowledge_chunks",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "document_id",
            sa.Integer(),
            sa.ForeignKey("knowledge_documents.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column("chunk_index", sa.Integer(), nullable=False),
        sa.Column("text", sa.Text(), nullable=False),
        sa.Column("embedding", Vector(1024)),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("now()")),
    )
    op.execute(
        "CREATE INDEX ix_knowledge_chunks_embedding_hnsw ON knowledge_chunks "
        "USING hnsw (embedding vector_cosine_ops)"
    )

    # === Настройки AI-агентов (управление из админ-панели) ===
    op.create_table(
        "agent_settings",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("agent_key", sa.String(20), nullable=False, unique=True),
        sa.Column("display_name", sa.String(200), nullable=False),
        sa.Column("description", sa.Text()),
        sa.Column("is_enabled", sa.Boolean(), server_default=sa.text("true")),
        sa.Column("config", sa.JSON(), server_default="{}"),
        # пороги, списки ключевых слов, правила эскалации
        sa.Column("prompt_template", sa.Text()),
        sa.Column("updated_by_id", sa.Integer(), sa.ForeignKey("users.id")),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.text("now()")),
    )


def downgrade() -> None:
    op.drop_table("agent_settings")
    op.execute("DROP INDEX IF EXISTS ix_knowledge_chunks_embedding_hnsw")
    op.drop_table("knowledge_chunks")
    op.drop_table("knowledge_documents")
    op.drop_table("notifications")
    op.drop_table("appeal_events")
    op.drop_table("appeal_attachments")
    op.drop_table("integrations")
    op.drop_column("social_posts", "source_id")
    op.drop_table("social_sources")

    op.alter_column("appeal_clusters", "requester_count", new_column_name="citizen_count")
    op.drop_column("users", "requester_id")
    op.alter_column("users", "department_id", new_column_name="ministry_id")

    op.alter_column("appeals", "from_repeat_complainant", new_column_name="from_querulant")
    op.alter_column("appeals", "campaign_cluster_id", new_column_name="infodrop_cluster_id")
    op.alter_column("appeals", "campaign_score", new_column_name="infodrop_score")
    op.alter_column("appeals", "is_campaign", new_column_name="is_infodrop")
    op.alter_column("appeals", "department_id", new_column_name="ministry_id")
    op.alter_column("appeals", "requester_id", new_column_name="citizen_id")

    op.drop_column("departments", "department_type")
    op.rename_table("departments", "ministries")

    op.drop_column("requesters", "affiliation")
    op.drop_column("requesters", "requester_type")
    op.alter_column("requesters", "repeat_score", new_column_name="querulant_score")
    op.alter_column("requesters", "is_repeat_complainant", new_column_name="is_querulant")
    op.alter_column("requesters", "identifier_hash", new_column_name="iin_hash")
    op.rename_table("requesters", "citizens")
