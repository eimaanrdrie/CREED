"""R87 ownership and responsibility registry

Revision ID: f2a3b4c5d6e7
Revises: e1f2a3b4c5d6
Create Date: 2026-08-20 09:12:00
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "f2a3b4c5d6e7"
down_revision: Union[str, None] = "e1f2a3b4c5d6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "responsibility_assignments",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("scope_type", sa.String(length=40), nullable=False),
        sa.Column("scope_id", sa.String(length=36), nullable=False),
        sa.Column("responsibility_type", sa.String(length=60), nullable=False),
        sa.Column("authority_id", sa.String(length=36), nullable=False),
        sa.Column("team_name", sa.String(length=180), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["authority_id"], ["human_authorities.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("scope_type", "scope_id", "responsibility_type", name="uq_responsibility_scope_role"),
    )
    op.create_index(op.f("ix_responsibility_assignments_scope_type"), "responsibility_assignments", ["scope_type"], unique=False)
    op.create_index(op.f("ix_responsibility_assignments_responsibility_type"), "responsibility_assignments", ["responsibility_type"], unique=False)
    op.create_index(op.f("ix_responsibility_assignments_authority_id"), "responsibility_assignments", ["authority_id"], unique=False)
    op.create_index("ix_responsibility_scope", "responsibility_assignments", ["scope_type", "scope_id"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_responsibility_scope", table_name="responsibility_assignments")
    op.drop_index(op.f("ix_responsibility_assignments_authority_id"), table_name="responsibility_assignments")
    op.drop_index(op.f("ix_responsibility_assignments_responsibility_type"), table_name="responsibility_assignments")
    op.drop_index(op.f("ix_responsibility_assignments_scope_type"), table_name="responsibility_assignments")
    op.drop_table("responsibility_assignments")
