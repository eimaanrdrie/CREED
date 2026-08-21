"""R89 product registry active status

Revision ID: g3b4c5d6e7f8
Revises: f2a3b4c5d6e7
Create Date: 2026-08-20 18:10:00
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "g3b4c5d6e7f8"
down_revision: Union[str, None] = "f2a3b4c5d6e7"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("products", sa.Column("active", sa.Boolean(), nullable=False, server_default=sa.true()))
    op.create_index(op.f("ix_products_active"), "products", ["active"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_products_active"), table_name="products")
    op.drop_column("products", "active")
