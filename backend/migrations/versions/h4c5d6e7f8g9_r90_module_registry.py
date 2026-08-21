"""R90 module registry active status

Revision ID: h4c5d6e7f8g9
Revises: g3b4c5d6e7f8
Create Date: 2026-08-20 18:25:00
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "h4c5d6e7f8g9"
down_revision: Union[str, None] = "g3b4c5d6e7f8"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("modules", sa.Column("active", sa.Boolean(), nullable=False, server_default=sa.true()))
    op.create_index(op.f("ix_modules_active"), "modules", ["active"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_modules_active"), table_name="modules")
    op.drop_column("modules", "active")
