"""Add tenant boundaries to persisted resources.

Revision ID: 0002_tenant_isolation
Revises: 0001_initial
"""
from alembic import op
import sqlalchemy as sa

revision = "0002_tenant_isolation"
down_revision = "0001_initial"
branch_labels = None
depends_on = None

TABLES = ("services", "telemetry_events", "incidents", "runbooks", "document_chunks", "audit_events", "evaluation_runs")


def upgrade() -> None:
    inspector = sa.inspect(op.get_bind())
    for table in TABLES:
        columns = {column["name"] for column in inspector.get_columns(table)}
        indexes = {index["name"] for index in inspector.get_indexes(table)}
        if "tenant_id" not in columns:
            op.add_column(table, sa.Column("tenant_id", sa.String(length=120), nullable=False, server_default="demo"))
        if f"ix_{table}_tenant_id" not in indexes:
            op.create_index(f"ix_{table}_tenant_id", table, ["tenant_id"])


def downgrade() -> None:
    for table in reversed(TABLES):
        op.drop_index(f"ix_{table}_tenant_id", table_name=table)
        op.drop_column(table, "tenant_id")
