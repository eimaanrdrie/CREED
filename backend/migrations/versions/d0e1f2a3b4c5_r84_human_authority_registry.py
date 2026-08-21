"""R84 human authority registry

Revision ID: d0e1f2a3b4c5
Revises: cfd6e75baf98
Create Date: 2026-08-19 22:40:00
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "d0e1f2a3b4c5"
down_revision: Union[str, None] = "cfd6e75baf98"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "human_authorities",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("principal", sa.String(length=180), nullable=False),
        sa.Column("display_name", sa.String(length=180), nullable=False),
        sa.Column("role_title", sa.String(length=180), nullable=False),
        sa.Column("active", sa.Boolean(), nullable=False),
        sa.Column("can_submit_human_decision", sa.Boolean(), nullable=False),
        sa.Column("can_approve_learning", sa.Boolean(), nullable=False),
        sa.Column("can_authorize_recall", sa.Boolean(), nullable=False),
        sa.Column("metadata_json", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_human_authorities_principal"), "human_authorities", ["principal"], unique=True)
    op.create_index(op.f("ix_human_authorities_display_name"), "human_authorities", ["display_name"], unique=False)
    op.create_index(op.f("ix_human_authorities_active"), "human_authorities", ["active"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_human_authorities_active"), table_name="human_authorities")
    op.drop_index(op.f("ix_human_authorities_display_name"), table_name="human_authorities")
    op.drop_index(op.f("ix_human_authorities_principal"), table_name="human_authorities")
    op.drop_table("human_authorities")
