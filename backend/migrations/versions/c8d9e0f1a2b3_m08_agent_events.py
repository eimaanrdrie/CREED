"""M08 persistent agent execution events

Revision ID: c8d9e0f1a2b3
Revises: b7c8d9e0f1a2
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = "c8d9e0f1a2b3"
down_revision: Union[str, None] = "b7c8d9e0f1a2"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "agent_events",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("agent_run_id", sa.String(length=36), nullable=False),
        sa.Column("agent_step_id", sa.String(length=36), nullable=True),
        sa.Column("event_seq", sa.Integer(), nullable=False),
        sa.Column("agent_name", sa.String(length=140), nullable=False),
        sa.Column("status", sa.String(length=40), nullable=False),
        sa.Column("message", sa.Text(), nullable=True),
        sa.Column("metadata_json", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["agent_run_id"], ["agent_runs.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["agent_step_id"], ["agent_steps.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("agent_run_id", "event_seq", name="uq_agent_event_run_seq"),
    )
    op.create_index("ix_agent_event_run_seq", "agent_events", ["agent_run_id", "event_seq"], unique=False)
    op.create_index(op.f("ix_agent_events_agent_run_id"), "agent_events", ["agent_run_id"], unique=False)
    op.create_index(op.f("ix_agent_events_agent_step_id"), "agent_events", ["agent_step_id"], unique=False)
    op.create_index(op.f("ix_agent_events_status"), "agent_events", ["status"], unique=False)
    op.create_index(op.f("ix_agent_events_created_at"), "agent_events", ["created_at"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_agent_events_created_at"), table_name="agent_events")
    op.drop_index(op.f("ix_agent_events_status"), table_name="agent_events")
    op.drop_index(op.f("ix_agent_events_agent_step_id"), table_name="agent_events")
    op.drop_index(op.f("ix_agent_events_agent_run_id"), table_name="agent_events")
    op.drop_index("ix_agent_event_run_seq", table_name="agent_events")
    op.drop_table("agent_events")
