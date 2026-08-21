"""document ingestion fields

Revision ID: 9e34a4c7d9b2
Revises: fd5e3c74bccf
Create Date: 2026-08-15 16:50:00
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = "9e34a4c7d9b2"
down_revision: Union[str, None] = "fd5e3c74bccf"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table("evidence_documents") as batch_op:
        batch_op.add_column(sa.Column("original_filename", sa.String(length=300), nullable=True))
        batch_op.add_column(sa.Column("mime_type", sa.String(length=180), nullable=True))
        batch_op.add_column(sa.Column("file_size", sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column("storage_path", sa.Text(), nullable=True))
        batch_op.add_column(sa.Column("parse_status", sa.String(length=40), server_default="PARSED", nullable=False))
        batch_op.add_column(sa.Column("parse_error", sa.Text(), nullable=True))
        batch_op.add_column(sa.Column("extracted_text", sa.Text(), nullable=True))
        batch_op.add_column(sa.Column("char_count", sa.Integer(), server_default="0", nullable=False))
        batch_op.create_index("ix_evidence_documents_parse_status", ["parse_status"], unique=False)


def downgrade() -> None:
    with op.batch_alter_table("evidence_documents") as batch_op:
        batch_op.drop_index("ix_evidence_documents_parse_status")
        batch_op.drop_column("char_count")
        batch_op.drop_column("extracted_text")
        batch_op.drop_column("parse_error")
        batch_op.drop_column("parse_status")
        batch_op.drop_column("storage_path")
        batch_op.drop_column("file_size")
        batch_op.drop_column("mime_type")
        batch_op.drop_column("original_filename")
