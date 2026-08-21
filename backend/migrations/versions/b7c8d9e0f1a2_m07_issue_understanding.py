"""M07 Qwen issue understanding records

Revision ID: b7c8d9e0f1a2
Revises: a6b7c8d9e0f1
Create Date: 2026-08-15
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "b7c8d9e0f1a2"
down_revision: Union[str, None] = "a6b7c8d9e0f1"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "issue_understandings",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("issue_id", sa.String(length=36), nullable=False),
        sa.Column("qwen_run_id", sa.String(length=140), nullable=False),
        sa.Column("input_hash", sa.String(length=64), nullable=False),
        sa.Column("configured_model", sa.String(length=180), nullable=False),
        sa.Column("actual_model", sa.String(length=180), nullable=True),
        sa.Column("duration_ms", sa.Float(), nullable=True),
        sa.Column("prompt_eval_count", sa.Integer(), nullable=True),
        sa.Column("eval_count", sa.Integer(), nullable=True),
        sa.Column("client_name", sa.String(length=180), nullable=True),
        sa.Column("product", sa.String(length=180), nullable=True),
        sa.Column("module", sa.String(length=180), nullable=True),
        sa.Column("issue_type", sa.String(length=40), nullable=False),
        sa.Column("summary", sa.Text(), nullable=False),
        sa.Column("suspected_function", sa.String(length=300), nullable=True),
        sa.Column("keywords_json", sa.JSON(), nullable=False),
        sa.Column("severity", sa.String(length=40), nullable=False),
        sa.Column("confidence", sa.Float(), nullable=False),
        sa.Column("model_output_json", sa.JSON(), nullable=False),
        sa.Column("status", sa.String(length=40), nullable=False, server_default="AI_GENERATED"),
        sa.Column("human_verified_by", sa.String(length=180), nullable=True),
        sa.Column("human_verified_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["issue_id"], ["support_issues.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("qwen_run_id", name="uq_issue_understanding_qwen_run"),
    )
    op.create_index("ix_issue_understandings_issue_id", "issue_understandings", ["issue_id"], unique=False)
    op.create_index("ix_issue_understandings_status", "issue_understandings", ["status"], unique=False)
    op.create_index("ix_issue_understanding_issue_created", "issue_understandings", ["issue_id", "created_at"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_issue_understanding_issue_created", table_name="issue_understandings")
    op.drop_index("ix_issue_understandings_status", table_name="issue_understandings")
    op.drop_index("ix_issue_understandings_issue_id", table_name="issue_understandings")
    op.drop_table("issue_understandings")
