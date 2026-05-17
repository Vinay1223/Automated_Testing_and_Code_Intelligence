"""initial schema

Revision ID: 0001_initial
Revises:
Create Date: 2026-05-17 00:00:00.000000
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "0001_initial"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "runs",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("org_id", sa.String(length=64), index=True),
        sa.Column("repo", sa.String(length=255), index=True),
        sa.Column("function_name", sa.String(length=255), index=True),
        sa.Column("framework", sa.String(length=32), nullable=False),
        sa.Column("language", sa.String(length=32), nullable=False),
        sa.Column("state", sa.String(length=32), nullable=False, index=True),
        sa.Column("attempts", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("final_test_code", sa.Text()),
        sa.Column("final_explanation", sa.Text()),
        sa.Column("payload", sa.JSON(), nullable=False, server_default="{}"),
        sa.Column("error", sa.Text()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_table(
        "usage_events",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("org_id", sa.String(length=64), index=True, nullable=False),
        sa.Column("kind", sa.String(length=32), nullable=False),
        sa.Column("quantity", sa.Integer(), nullable=False),
        sa.Column("stripe_event_id", sa.String(length=128), index=True),
        sa.Column("occurred_at", sa.DateTime(timezone=True), server_default=sa.func.now(), index=True),
    )


def downgrade() -> None:
    op.drop_table("usage_events")
    op.drop_table("runs")
