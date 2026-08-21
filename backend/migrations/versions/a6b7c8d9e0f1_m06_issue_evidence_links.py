"""M06 issue capsule evidence links

Revision ID: a6b7c8d9e0f1
Revises: 4f5d6a7b8c9d
Create Date: 2026-08-15
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "a6b7c8d9e0f1"
down_revision: Union[str, None] = "4f5d6a7b8c9d"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "issue_evidence_links",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("issue_id", sa.String(length=36), nullable=False),
        sa.Column("document_id", sa.String(length=36), nullable=False),
        sa.Column("relationship", sa.String(length=80), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["document_id"], ["evidence_documents.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["issue_id"], ["support_issues.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("issue_id", "document_id", name="uq_issue_evidence_link"),
    )
    op.create_index("ix_issue_evidence_issue", "issue_evidence_links", ["issue_id"], unique=False)
    op.create_index("ix_issue_evidence_document", "issue_evidence_links", ["document_id"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_issue_evidence_document", table_name="issue_evidence_links")
    op.drop_index("ix_issue_evidence_issue", table_name="issue_evidence_links")
    op.drop_table("issue_evidence_links")
