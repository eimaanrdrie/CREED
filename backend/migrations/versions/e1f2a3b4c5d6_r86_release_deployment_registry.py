"""R86 release deployment registry

Revision ID: e1f2a3b4c5d6
Revises: d0e1f2a3b4c5
Create Date: 2026-08-20 09:05:00
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "e1f2a3b4c5d6"
down_revision: Union[str, None] = "d0e1f2a3b4c5"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "implementation_deployments",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("implementation_id", sa.String(length=36), nullable=False),
        sa.Column("environment", sa.String(length=40), nullable=False),
        sa.Column("status", sa.String(length=40), nullable=False),
        sa.Column("deployed_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("deployment_reference", sa.String(length=140), nullable=True),
        sa.Column("evidence_document_id", sa.String(length=36), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["evidence_document_id"], ["evidence_documents.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["implementation_id"], ["implementations.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_implementation_deployments_implementation_id"), "implementation_deployments", ["implementation_id"], unique=False)
    op.create_index(op.f("ix_implementation_deployments_environment"), "implementation_deployments", ["environment"], unique=False)
    op.create_index(op.f("ix_implementation_deployments_status"), "implementation_deployments", ["status"], unique=False)
    op.create_index(op.f("ix_implementation_deployments_deployed_at"), "implementation_deployments", ["deployed_at"], unique=False)
    op.create_index(op.f("ix_implementation_deployments_deployment_reference"), "implementation_deployments", ["deployment_reference"], unique=False)
    op.create_index(op.f("ix_implementation_deployments_evidence_document_id"), "implementation_deployments", ["evidence_document_id"], unique=False)
    op.create_index("ix_deployment_impl_env_time", "implementation_deployments", ["implementation_id", "environment", "deployed_at"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_deployment_impl_env_time", table_name="implementation_deployments")
    op.drop_index(op.f("ix_implementation_deployments_evidence_document_id"), table_name="implementation_deployments")
    op.drop_index(op.f("ix_implementation_deployments_deployment_reference"), table_name="implementation_deployments")
    op.drop_index(op.f("ix_implementation_deployments_deployed_at"), table_name="implementation_deployments")
    op.drop_index(op.f("ix_implementation_deployments_status"), table_name="implementation_deployments")
    op.drop_index(op.f("ix_implementation_deployments_environment"), table_name="implementation_deployments")
    op.drop_index(op.f("ix_implementation_deployments_implementation_id"), table_name="implementation_deployments")
    op.drop_table("implementation_deployments")
