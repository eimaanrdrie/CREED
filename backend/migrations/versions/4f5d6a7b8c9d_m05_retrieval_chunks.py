"""M05 retrieval chunks and vector-ready index metadata.

Revision ID: 4f5d6a7b8c9d
Revises: 9e34a4c7d9b2
"""
from alembic import op
import sqlalchemy as sa

revision = "4f5d6a7b8c9d"
down_revision = "9e34a4c7d9b2"
branch_labels = None
depends_on = None


def upgrade():
    bind = op.get_bind()
    if bind.dialect.name == "postgresql":
        op.execute("CREATE EXTENSION IF NOT EXISTS vector")
    with op.batch_alter_table("evidence_documents") as batch:
        batch.add_column(sa.Column("index_status", sa.String(length=40), nullable=False, server_default="PENDING"))
        batch.add_column(sa.Column("indexed_at", sa.DateTime(timezone=True), nullable=True))
        batch.add_column(sa.Column("chunk_count", sa.Integer(), nullable=False, server_default="0"))
        batch.add_column(sa.Column("embedding_model", sa.String(length=180), nullable=True))
        batch.add_column(sa.Column("embedding_degraded", sa.Boolean(), nullable=False, server_default=sa.false()))
        batch.create_index("ix_evidence_documents_index_status", ["index_status"])
    op.create_table(
        "document_chunks",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("document_id", sa.String(length=36), sa.ForeignKey("evidence_documents.id", ondelete="CASCADE"), nullable=False),
        sa.Column("chunk_index", sa.Integer(), nullable=False),
        sa.Column("text", sa.Text(), nullable=False),
        sa.Column("start_char", sa.Integer(), nullable=False),
        sa.Column("end_char", sa.Integer(), nullable=False),
        sa.Column("chunk_hash", sa.String(length=128), nullable=False),
        sa.Column("embedding_vector", sa.Text(), nullable=False),
        sa.Column("embedding_provider", sa.String(length=80), nullable=False),
        sa.Column("embedding_model", sa.String(length=180), nullable=False),
        sa.Column("embedding_dimensions", sa.Integer(), nullable=False),
        sa.Column("embedding_degraded", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("metadata_json", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("document_id", "chunk_index", name="uq_document_chunk_index"),
    )
    op.create_index("ix_document_chunk_document", "document_chunks", ["document_id"])
    op.create_index("ix_document_chunk_hash", "document_chunks", ["chunk_hash"])
    if bind.dialect.name == "postgresql":
        op.execute("ALTER TABLE document_chunks ALTER COLUMN embedding_vector TYPE vector(384) USING embedding_vector::vector")
        op.execute("CREATE INDEX ix_document_chunks_embedding_hnsw ON document_chunks USING hnsw (embedding_vector vector_cosine_ops)")


def downgrade():
    op.drop_table("document_chunks")
    with op.batch_alter_table("evidence_documents") as batch:
        batch.drop_index("ix_evidence_documents_index_status")
        batch.drop_column("embedding_degraded")
        batch.drop_column("embedding_model")
        batch.drop_column("chunk_count")
        batch.drop_column("indexed_at")
        batch.drop_column("index_status")
