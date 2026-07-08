"""Enterprise multi-tenancy и оргиерархия (Phase 2).

Аддитивная, неразрушающая миграция:
- новые таблицы: tenants, regions, healthcare_organizations, hospitals;
- новые nullable-колонки tenant_id/hospital_id на appeals, departments, users,
  requesters (существующие данные не затрагиваются, backfill — в enterprise seed).

Revision ID: 004
Revises: 003
"""
import sqlalchemy as sa
from alembic import op

revision = "004"
down_revision = "003"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "tenants",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("slug", sa.String(80), nullable=False),
        sa.Column("plan", sa.String(30), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=True),
        sa.Column("settings", sa.JSON(), nullable=True),
        sa.Column("branding", sa.JSON(), nullable=True),
        sa.Column("ai_config", sa.JSON(), nullable=True),
        sa.Column("contact_email", sa.String(255), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
    )
    op.create_index("ix_tenants_slug", "tenants", ["slug"], unique=True)

    op.create_table(
        "regions",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(120), nullable=False),
        sa.Column("code", sa.String(20), nullable=True),
        sa.Column("center", sa.String(120), nullable=True),
        sa.Column("population", sa.Integer(), nullable=True),
        sa.Column("lat", sa.Float(), nullable=True),
        sa.Column("lng", sa.Float(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
    )
    op.create_index("ix_regions_name", "regions", ["name"], unique=True)
    op.create_index("ix_regions_code", "regions", ["code"], unique=True)

    op.create_table(
        "healthcare_organizations",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("tenant_id", sa.Integer(), sa.ForeignKey("tenants.id"), nullable=True),
        sa.Column("region_id", sa.Integer(), sa.ForeignKey("regions.id"), nullable=True),
        sa.Column("name", sa.String(300), nullable=False),
        sa.Column("code", sa.String(40), nullable=True),
        sa.Column("org_type", sa.String(50), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=True),
        sa.Column("contact_email", sa.String(255), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
    )
    op.create_index("ix_healthcare_organizations_tenant_id", "healthcare_organizations", ["tenant_id"])
    op.create_index("ix_healthcare_organizations_region_id", "healthcare_organizations", ["region_id"])
    op.create_index("ix_healthcare_organizations_code", "healthcare_organizations", ["code"])

    op.create_table(
        "hospitals",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("tenant_id", sa.Integer(), sa.ForeignKey("tenants.id"), nullable=True),
        sa.Column(
            "organization_id", sa.Integer(),
            sa.ForeignKey("healthcare_organizations.id"), nullable=True,
        ),
        sa.Column("region_id", sa.Integer(), sa.ForeignKey("regions.id"), nullable=True),
        sa.Column("name", sa.String(300), nullable=False),
        sa.Column("code", sa.String(40), nullable=True),
        sa.Column("hospital_type", sa.String(50), nullable=True),
        sa.Column("beds", sa.Integer(), nullable=True),
        sa.Column("address", sa.String(400), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
    )
    op.create_index("ix_hospitals_tenant_id", "hospitals", ["tenant_id"])
    op.create_index("ix_hospitals_organization_id", "hospitals", ["organization_id"])
    op.create_index("ix_hospitals_region_id", "hospitals", ["region_id"])
    op.create_index("ix_hospitals_code", "hospitals", ["code"])

    # --- Аддитивные колонки на существующих таблицах ---
    op.add_column("appeals", sa.Column("tenant_id", sa.Integer(), nullable=True))
    op.add_column("appeals", sa.Column("hospital_id", sa.Integer(), nullable=True))
    op.create_index("ix_appeals_tenant_id", "appeals", ["tenant_id"])
    op.create_index("ix_appeals_hospital_id", "appeals", ["hospital_id"])
    op.create_foreign_key("fk_appeals_tenant", "appeals", "tenants", ["tenant_id"], ["id"])
    op.create_foreign_key("fk_appeals_hospital", "appeals", "hospitals", ["hospital_id"], ["id"])

    op.add_column("departments", sa.Column("tenant_id", sa.Integer(), nullable=True))
    op.add_column("departments", sa.Column("hospital_id", sa.Integer(), nullable=True))
    op.create_index("ix_departments_tenant_id", "departments", ["tenant_id"])
    op.create_index("ix_departments_hospital_id", "departments", ["hospital_id"])
    op.create_foreign_key("fk_departments_tenant", "departments", "tenants", ["tenant_id"], ["id"])
    op.create_foreign_key("fk_departments_hospital", "departments", "hospitals", ["hospital_id"], ["id"])

    op.add_column("users", sa.Column("tenant_id", sa.Integer(), nullable=True))
    op.create_index("ix_users_tenant_id", "users", ["tenant_id"])
    op.create_foreign_key("fk_users_tenant", "users", "tenants", ["tenant_id"], ["id"])

    op.add_column("requesters", sa.Column("tenant_id", sa.Integer(), nullable=True))
    op.create_index("ix_requesters_tenant_id", "requesters", ["tenant_id"])
    op.create_foreign_key("fk_requesters_tenant", "requesters", "tenants", ["tenant_id"], ["id"])


def downgrade() -> None:
    op.drop_constraint("fk_requesters_tenant", "requesters", type_="foreignkey")
    op.drop_index("ix_requesters_tenant_id", table_name="requesters")
    op.drop_column("requesters", "tenant_id")

    op.drop_constraint("fk_users_tenant", "users", type_="foreignkey")
    op.drop_index("ix_users_tenant_id", table_name="users")
    op.drop_column("users", "tenant_id")

    op.drop_constraint("fk_departments_hospital", "departments", type_="foreignkey")
    op.drop_constraint("fk_departments_tenant", "departments", type_="foreignkey")
    op.drop_index("ix_departments_hospital_id", table_name="departments")
    op.drop_index("ix_departments_tenant_id", table_name="departments")
    op.drop_column("departments", "hospital_id")
    op.drop_column("departments", "tenant_id")

    op.drop_constraint("fk_appeals_hospital", "appeals", type_="foreignkey")
    op.drop_constraint("fk_appeals_tenant", "appeals", type_="foreignkey")
    op.drop_index("ix_appeals_hospital_id", table_name="appeals")
    op.drop_index("ix_appeals_tenant_id", table_name="appeals")
    op.drop_column("appeals", "hospital_id")
    op.drop_column("appeals", "tenant_id")

    op.drop_table("hospitals")
    op.drop_table("healthcare_organizations")
    op.drop_index("ix_regions_code", table_name="regions")
    op.drop_index("ix_regions_name", table_name="regions")
    op.drop_table("regions")
    op.drop_index("ix_tenants_slug", table_name="tenants")
    op.drop_table("tenants")
