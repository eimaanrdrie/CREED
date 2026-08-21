"""R94-M05 run-scoped investigations

Revision ID: e5f6a7b8c9d0
Revises: h4c5d6e7f8g9
Create Date: 2026-08-20
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "e5f6a7b8c9d0"
down_revision: Union[str, None] = "h4c5d6e7f8g9"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add the run identity first so existing investigation history can be backfilled
    # from the already run-scoped InvestigationDetail rows introduced in M20.
    with op.batch_alter_table("investigations") as batch_op:
        batch_op.add_column(sa.Column("agent_run_id", sa.String(length=36), nullable=True))
        batch_op.create_index("ix_investigations_agent_run_id", ["agent_run_id"], unique=False)
        batch_op.create_foreign_key(
            "fk_investigations_agent_run_id_agent_runs",
            "agent_runs",
            ["agent_run_id"],
            ["id"],
            ondelete="SET NULL",
        )

    op.execute(
        sa.text(
            """
            UPDATE investigations
            SET agent_run_id = (
                SELECT investigation_details.agent_run_id
                FROM investigation_details
                WHERE investigation_details.investigation_id = investigations.id
                  AND investigation_details.agent_run_id IS NOT NULL
                LIMIT 1
            )
            WHERE agent_run_id IS NULL
            """
        )
    )

    # The old issue-wide uniqueness prevented a second legitimate analysis run from
    # creating a fresh investigation for the same implementation. Scope uniqueness
    # to the run instead. NULL remains permitted for legacy/manual rows.
    with op.batch_alter_table("investigations") as batch_op:
        batch_op.drop_constraint("uq_issue_implementation_investigation", type_="unique")
        batch_op.create_unique_constraint(
            "uq_run_implementation_investigation",
            ["agent_run_id", "implementation_id"],
        )


def downgrade() -> None:
    # Downgrade can only restore issue-wide uniqueness if the database does not
    # contain multiple run-scoped investigations for the same issue/implementation.
    with op.batch_alter_table("investigations") as batch_op:
        batch_op.drop_constraint("uq_run_implementation_investigation", type_="unique")
        batch_op.create_unique_constraint(
            "uq_issue_implementation_investigation",
            ["issue_id", "implementation_id"],
        )
        batch_op.drop_constraint("fk_investigations_agent_run_id_agent_runs", type_="foreignkey")
        batch_op.drop_index("ix_investigations_agent_run_id")
        batch_op.drop_column("agent_run_id")
