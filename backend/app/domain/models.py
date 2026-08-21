from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import (
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    JSON,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.types import TypeDecorator, UserDefinedType
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.domain.enums import (
    AgentStatus,
    InvestigationStatus,
    IssueSeverity,
    IssueStatus,
    IssueType,
    LearningStatus,
    MethodVersionStatus,
)


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def uuid_str() -> str:
    return str(uuid.uuid4())


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False)


class _PostgresVector(UserDefinedType):
    cache_ok = True

    def __init__(self, dimensions: int) -> None:
        self.dimensions = dimensions

    def get_col_spec(self, **_kw: Any) -> str:
        return f"vector({self.dimensions})"


class EmbeddingVectorType(TypeDecorator):
    impl = Text
    cache_ok = True

    def __init__(self, dimensions: int) -> None:
        super().__init__()
        self.dimensions = dimensions

    def load_dialect_impl(self, dialect):
        if dialect.name == "postgresql":
            return dialect.type_descriptor(_PostgresVector(self.dimensions))
        return dialect.type_descriptor(Text())

    def process_bind_param(self, value: Any, dialect) -> Any:
        if value is None:
            return None
        if isinstance(value, (list, tuple)):
            return "[" + ",".join(f"{float(item):.9f}" for item in value) + "]"
        return value

    def process_result_value(self, value: Any, dialect) -> Any:
        return value


class Client(Base, TimestampMixin):
    __tablename__ = "clients"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid_str)
    name: Mapped[str] = mapped_column(String(180), unique=True, index=True, nullable=False)
    client_type: Mapped[str] = mapped_column(String(80), default="BANK", nullable=False)
    metadata_json: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)

    issues: Mapped[list[SupportIssue]] = relationship(back_populates="client")
    implementations: Mapped[list[Implementation]] = relationship(back_populates="client")




class HumanAuthority(Base, TimestampMixin):
    __tablename__ = "human_authorities"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid_str)
    principal: Mapped[str] = mapped_column(String(180), unique=True, index=True, nullable=False)
    display_name: Mapped[str] = mapped_column(String(180), index=True, nullable=False)
    role_title: Mapped[str] = mapped_column(String(180), nullable=False)
    active: Mapped[bool] = mapped_column(Boolean, default=True, index=True, nullable=False)
    can_submit_human_decision: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    can_approve_learning: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    can_authorize_recall: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    metadata_json: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)


class ResponsibilityAssignment(Base, TimestampMixin):
    __tablename__ = "responsibility_assignments"
    __table_args__ = (
        UniqueConstraint("scope_type", "scope_id", "responsibility_type", name="uq_responsibility_scope_role"),
        Index("ix_responsibility_scope", "scope_type", "scope_id"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid_str)
    scope_type: Mapped[str] = mapped_column(String(40), index=True, nullable=False)
    scope_id: Mapped[str] = mapped_column(String(36), nullable=False)
    responsibility_type: Mapped[str] = mapped_column(String(60), index=True, nullable=False)
    authority_id: Mapped[str] = mapped_column(ForeignKey("human_authorities.id", ondelete="RESTRICT"), index=True, nullable=False)
    team_name: Mapped[str | None] = mapped_column(String(180))

    authority: Mapped[HumanAuthority] = relationship()


class Product(Base, TimestampMixin):
    __tablename__ = "products"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid_str)
    name: Mapped[str] = mapped_column(String(180), unique=True, index=True, nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    active: Mapped[bool] = mapped_column(default=True, index=True, nullable=False)

    modules: Mapped[list[Module]] = relationship(back_populates="product", cascade="all, delete-orphan")
    implementations: Mapped[list[Implementation]] = relationship(back_populates="product")


class Module(Base, TimestampMixin):
    __tablename__ = "modules"
    __table_args__ = (UniqueConstraint("product_id", "name", name="uq_module_product_name"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid_str)
    product_id: Mapped[str] = mapped_column(ForeignKey("products.id", ondelete="CASCADE"), index=True, nullable=False)
    name: Mapped[str] = mapped_column(String(180), index=True, nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    active: Mapped[bool] = mapped_column(default=True, index=True, nullable=False)

    product: Mapped[Product] = relationship(back_populates="modules")
    methods: Mapped[list[DeliveryMethod]] = relationship(back_populates="module")
    implementations: Mapped[list[Implementation]] = relationship(back_populates="module")


class SupportIssue(Base, TimestampMixin):
    __tablename__ = "support_issues"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid_str)
    external_ticket_id: Mapped[str | None] = mapped_column(String(120), index=True)
    client_id: Mapped[str | None] = mapped_column(ForeignKey("clients.id", ondelete="SET NULL"), index=True)
    title: Mapped[str] = mapped_column(String(300), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    issue_type: Mapped[str] = mapped_column(String(40), default=IssueType.UNKNOWN.value, index=True, nullable=False)
    severity: Mapped[str] = mapped_column(String(40), default=IssueSeverity.UNKNOWN.value, index=True, nullable=False)
    status: Mapped[str] = mapped_column(String(40), default=IssueStatus.OPEN.value, index=True, nullable=False)

    client: Mapped[Client | None] = relationship(back_populates="issues")
    evidence_links: Mapped[list[IssueEvidenceLink]] = relationship(back_populates="issue", cascade="all, delete-orphan")
    investigations: Mapped[list[Investigation]] = relationship(back_populates="issue")
    learning_proposals: Mapped[list[LearningProposal]] = relationship(back_populates="source_issue")
    agent_runs: Mapped[list[AgentRun]] = relationship(back_populates="issue")
    understandings: Mapped[list[IssueUnderstanding]] = relationship(back_populates="issue", cascade="all, delete-orphan")


class EvidenceDocument(Base, TimestampMixin):
    __tablename__ = "evidence_documents"
    __table_args__ = (Index("ix_evidence_source_hash", "source", "content_hash"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid_str)
    source: Mapped[str] = mapped_column(String(80), index=True, nullable=False)
    source_url: Mapped[str | None] = mapped_column(Text)
    title: Mapped[str] = mapped_column(String(300), index=True, nullable=False)
    document_type: Mapped[str] = mapped_column(String(80), index=True, nullable=False)
    version: Mapped[str | None] = mapped_column(String(80))
    content_hash: Mapped[str] = mapped_column(String(128), index=True, nullable=False)
    original_filename: Mapped[str | None] = mapped_column(String(300))
    mime_type: Mapped[str | None] = mapped_column(String(180))
    file_size: Mapped[int | None] = mapped_column(Integer)
    storage_path: Mapped[str | None] = mapped_column(Text)
    parse_status: Mapped[str] = mapped_column(String(40), default="PARSED", index=True, nullable=False)
    parse_error: Mapped[str | None] = mapped_column(Text)
    extracted_text: Mapped[str | None] = mapped_column(Text)
    char_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    uploaded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)
    metadata_json: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)
    index_status: Mapped[str] = mapped_column(String(40), default="PENDING", index=True, nullable=False)
    indexed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    chunk_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    embedding_model: Mapped[str | None] = mapped_column(String(180))
    embedding_degraded: Mapped[bool] = mapped_column(default=False, nullable=False)

    issue_links: Mapped[list[IssueEvidenceLink]] = relationship(back_populates="document", cascade="all, delete-orphan")


class IssueEvidenceLink(Base):
    __tablename__ = "issue_evidence_links"
    __table_args__ = (
        UniqueConstraint("issue_id", "document_id", name="uq_issue_evidence_link"),
        Index("ix_issue_evidence_issue", "issue_id"),
        Index("ix_issue_evidence_document", "document_id"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid_str)
    issue_id: Mapped[str] = mapped_column(ForeignKey("support_issues.id", ondelete="CASCADE"), nullable=False)
    document_id: Mapped[str] = mapped_column(ForeignKey("evidence_documents.id", ondelete="CASCADE"), nullable=False)
    link_type: Mapped[str] = mapped_column("relationship", String(80), default="ATTACHMENT", nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)

    issue: Mapped[SupportIssue] = relationship(back_populates="evidence_links")
    document: Mapped[EvidenceDocument] = relationship(back_populates="issue_links")


class IssueUnderstanding(Base, TimestampMixin):
    __tablename__ = "issue_understandings"
    __table_args__ = (
        Index("ix_issue_understanding_issue_created", "issue_id", "created_at"),
        UniqueConstraint("qwen_run_id", name="uq_issue_understanding_qwen_run"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid_str)
    issue_id: Mapped[str] = mapped_column(ForeignKey("support_issues.id", ondelete="CASCADE"), index=True, nullable=False)
    qwen_run_id: Mapped[str] = mapped_column(String(140), nullable=False)
    input_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    configured_model: Mapped[str] = mapped_column(String(180), nullable=False)
    actual_model: Mapped[str | None] = mapped_column(String(180))
    duration_ms: Mapped[float | None] = mapped_column(Float)
    prompt_eval_count: Mapped[int | None] = mapped_column(Integer)
    eval_count: Mapped[int | None] = mapped_column(Integer)

    client_name: Mapped[str | None] = mapped_column(String(180))
    product: Mapped[str | None] = mapped_column(String(180))
    module: Mapped[str | None] = mapped_column(String(180))
    issue_type: Mapped[str] = mapped_column(String(40), nullable=False)
    summary: Mapped[str] = mapped_column(Text, nullable=False)
    suspected_function: Mapped[str | None] = mapped_column(String(300))
    keywords_json: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)
    severity: Mapped[str] = mapped_column(String(40), nullable=False)
    confidence: Mapped[float] = mapped_column(Float, nullable=False)
    model_output_json: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)

    status: Mapped[str] = mapped_column(String(40), default="AI_GENERATED", index=True, nullable=False)
    human_verified_by: Mapped[str | None] = mapped_column(String(180))
    human_verified_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    issue: Mapped[SupportIssue] = relationship(back_populates="understandings")


class DeliveryMethod(Base, TimestampMixin):
    __tablename__ = "delivery_methods"
    __table_args__ = (UniqueConstraint("module_id", "name", name="uq_method_module_name"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid_str)
    module_id: Mapped[str] = mapped_column(ForeignKey("modules.id", ondelete="CASCADE"), index=True, nullable=False)
    name: Mapped[str] = mapped_column(String(220), index=True, nullable=False)
    description: Mapped[str | None] = mapped_column(Text)

    module: Mapped[Module] = relationship(back_populates="methods")
    versions: Mapped[list[MethodVersion]] = relationship(back_populates="method", cascade="all, delete-orphan")


class MethodVersion(Base, TimestampMixin):
    __tablename__ = "method_versions"
    __table_args__ = (UniqueConstraint("method_id", "version", name="uq_method_version"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid_str)
    method_id: Mapped[str] = mapped_column(ForeignKey("delivery_methods.id", ondelete="CASCADE"), index=True, nullable=False)
    version: Mapped[str] = mapped_column(String(80), nullable=False)
    status: Mapped[str] = mapped_column(String(40), default=MethodVersionStatus.DRAFT.value, index=True, nullable=False)
    summary: Mapped[str | None] = mapped_column(Text)
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    method: Mapped[DeliveryMethod] = relationship(back_populates="versions")
    learning_proposals: Mapped[list[LearningProposal]] = relationship(back_populates="proposed_method_version")
    recalls: Mapped[list[RecallNotice]] = relationship(back_populates="revoked_version")


class Implementation(Base, TimestampMixin):
    __tablename__ = "implementations"
    __table_args__ = (
        UniqueConstraint("client_id", "module_id", "release_version", name="uq_implementation_release"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid_str)
    client_id: Mapped[str] = mapped_column(ForeignKey("clients.id", ondelete="CASCADE"), index=True, nullable=False)
    product_id: Mapped[str] = mapped_column(ForeignKey("products.id", ondelete="CASCADE"), index=True, nullable=False)
    module_id: Mapped[str] = mapped_column(ForeignKey("modules.id", ondelete="CASCADE"), index=True, nullable=False)
    name: Mapped[str] = mapped_column(String(220), nullable=False)
    release_version: Mapped[str] = mapped_column(String(80), nullable=False)
    status: Mapped[str] = mapped_column(String(40), default="ACTIVE", index=True, nullable=False)
    metadata_json: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)

    client: Mapped[Client] = relationship(back_populates="implementations")
    product: Mapped[Product] = relationship(back_populates="implementations")
    module: Mapped[Module] = relationship(back_populates="implementations")
    investigations: Mapped[list[Investigation]] = relationship(back_populates="implementation")
    deployments: Mapped[list[ImplementationDeployment]] = relationship(back_populates="implementation", cascade="all, delete-orphan")


class ImplementationDeployment(Base, TimestampMixin):
    __tablename__ = "implementation_deployments"
    __table_args__ = (
        Index("ix_deployment_impl_env_time", "implementation_id", "environment", "deployed_at"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid_str)
    implementation_id: Mapped[str] = mapped_column(ForeignKey("implementations.id", ondelete="CASCADE"), index=True, nullable=False)
    environment: Mapped[str] = mapped_column(String(40), index=True, nullable=False)
    status: Mapped[str] = mapped_column(String(40), default="DEPLOYED", index=True, nullable=False)
    deployed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True, nullable=False)
    deployment_reference: Mapped[str | None] = mapped_column(String(140), index=True)
    evidence_document_id: Mapped[str | None] = mapped_column(ForeignKey("evidence_documents.id", ondelete="SET NULL"), index=True)
    notes: Mapped[str | None] = mapped_column(Text)

    implementation: Mapped[Implementation] = relationship(back_populates="deployments")
    evidence_document: Mapped[EvidenceDocument | None] = relationship()


class DependencyEdge(Base):
    __tablename__ = "dependency_edges"
    __table_args__ = (
        Index("ix_dependency_source", "source_type", "source_id"),
        Index("ix_dependency_target", "target_type", "target_id"),
        UniqueConstraint(
            "source_type",
            "source_id",
            "target_type",
            "target_id",
            "relationship",
            name="uq_dependency_edge",
        ),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid_str)
    source_type: Mapped[str] = mapped_column(String(80), nullable=False)
    source_id: Mapped[str] = mapped_column(String(36), nullable=False)
    target_type: Mapped[str] = mapped_column(String(80), nullable=False)
    target_id: Mapped[str] = mapped_column(String(36), nullable=False)
    relationship: Mapped[str] = mapped_column(String(120), index=True, nullable=False)
    confidence: Mapped[float] = mapped_column(Float, default=1.0, nullable=False)
    evidence_document_id: Mapped[str | None] = mapped_column(ForeignKey("evidence_documents.id", ondelete="SET NULL"), index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)


class Investigation(Base, TimestampMixin):
    __tablename__ = "investigations"
    __table_args__ = (
        UniqueConstraint("agent_run_id", "implementation_id", name="uq_run_implementation_investigation"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid_str)
    issue_id: Mapped[str] = mapped_column(ForeignKey("support_issues.id", ondelete="CASCADE"), index=True, nullable=False)
    # R94-M05: investigations are analysis-run artifacts, not issue-global state.
    # Nullable only for backward compatibility with legacy/manual rows and recall bootstrap data.
    agent_run_id: Mapped[str | None] = mapped_column(ForeignKey("agent_runs.id", ondelete="SET NULL"), index=True)
    implementation_id: Mapped[str] = mapped_column(ForeignKey("implementations.id", ondelete="CASCADE"), index=True, nullable=False)
    status: Mapped[str] = mapped_column(String(40), default=InvestigationStatus.QUEUED.value, index=True, nullable=False)
    risk_score: Mapped[float | None] = mapped_column(Float)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    issue: Mapped[SupportIssue] = relationship(back_populates="investigations")
    implementation: Mapped[Implementation] = relationship(back_populates="investigations")
    findings: Mapped[list[Finding]] = relationship(back_populates="investigation", cascade="all, delete-orphan")
    decisions: Mapped[list[HumanDecision]] = relationship(back_populates="investigation", cascade="all, delete-orphan")


class Finding(Base, TimestampMixin):
    __tablename__ = "findings"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid_str)
    investigation_id: Mapped[str] = mapped_column(ForeignKey("investigations.id", ondelete="CASCADE"), index=True, nullable=False)
    finding_type: Mapped[str] = mapped_column(String(100), index=True, nullable=False)
    statement: Mapped[str] = mapped_column(Text, nullable=False)
    confidence: Mapped[float | None] = mapped_column(Float)
    evidence_refs: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)

    investigation: Mapped[Investigation] = relationship(back_populates="findings")


class HumanDecision(Base):
    __tablename__ = "human_decisions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid_str)
    investigation_id: Mapped[str | None] = mapped_column(ForeignKey("investigations.id", ondelete="CASCADE"), index=True)
    decision: Mapped[str] = mapped_column(String(80), index=True, nullable=False)
    reviewer: Mapped[str] = mapped_column(String(180), nullable=False)
    reason: Mapped[str | None] = mapped_column(Text)
    decided_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)
    metadata_json: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)

    investigation: Mapped[Investigation | None] = relationship(back_populates="decisions")


class LearningProposal(Base, TimestampMixin):
    __tablename__ = "learning_proposals"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid_str)
    source_issue_id: Mapped[str] = mapped_column(ForeignKey("support_issues.id", ondelete="CASCADE"), index=True, nullable=False)
    proposed_method_version_id: Mapped[str | None] = mapped_column(ForeignKey("method_versions.id", ondelete="SET NULL"), index=True)
    status: Mapped[str] = mapped_column(String(40), default=LearningStatus.DRAFT.value, index=True, nullable=False)
    summary: Mapped[str] = mapped_column(Text, nullable=False)
    supporting_evidence_refs: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)

    source_issue: Mapped[SupportIssue] = relationship(back_populates="learning_proposals")
    proposed_method_version: Mapped[MethodVersion | None] = relationship(back_populates="learning_proposals")
    adoption_receipt: Mapped[AdoptionReceipt | None] = relationship(back_populates="learning", uselist=False)


class AdoptionReceipt(Base):
    __tablename__ = "adoption_receipts"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid_str)
    learning_id: Mapped[str] = mapped_column(ForeignKey("learning_proposals.id", ondelete="CASCADE"), unique=True, index=True, nullable=False)
    approved_by: Mapped[str] = mapped_column(String(180), nullable=False)
    approved_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)
    content_hash: Mapped[str] = mapped_column(String(128), unique=True, nullable=False)
    adoption_scope: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)

    learning: Mapped[LearningProposal] = relationship(back_populates="adoption_receipt")


class RecallNotice(Base):
    __tablename__ = "recall_notices"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid_str)
    revoked_version_id: Mapped[str] = mapped_column(ForeignKey("method_versions.id", ondelete="CASCADE"), index=True, nullable=False)
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    approved_by: Mapped[str] = mapped_column(String(180), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)
    content_hash: Mapped[str] = mapped_column(String(128), unique=True, nullable=False)
    status: Mapped[str] = mapped_column(String(40), default="ACTIVE", index=True, nullable=False)

    revoked_version: Mapped[MethodVersion] = relationship(back_populates="recalls")


class AgentRun(Base):
    __tablename__ = "agent_runs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid_str)
    graph_run_id: Mapped[str] = mapped_column(String(140), unique=True, index=True, nullable=False)
    issue_id: Mapped[str | None] = mapped_column(ForeignKey("support_issues.id", ondelete="SET NULL"), index=True)
    status: Mapped[str] = mapped_column(String(40), default=AgentStatus.QUEUED.value, index=True, nullable=False)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    input_summary: Mapped[str | None] = mapped_column(Text)
    output_summary: Mapped[str | None] = mapped_column(Text)
    error: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)

    issue: Mapped[SupportIssue | None] = relationship(back_populates="agent_runs")
    steps: Mapped[list[AgentStep]] = relationship(back_populates="agent_run", cascade="all, delete-orphan")
    events: Mapped[list[AgentEvent]] = relationship(back_populates="agent_run", cascade="all, delete-orphan")


class AgentStep(Base):
    __tablename__ = "agent_steps"
    __table_args__ = (Index("ix_agent_step_run_name", "agent_run_id", "agent_name"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid_str)
    agent_run_id: Mapped[str] = mapped_column(ForeignKey("agent_runs.id", ondelete="CASCADE"), index=True, nullable=False)
    agent_name: Mapped[str] = mapped_column(String(140), nullable=False)
    status: Mapped[str] = mapped_column(String(40), default=AgentStatus.QUEUED.value, index=True, nullable=False)
    sequence: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    input_summary: Mapped[str | None] = mapped_column(Text)
    output_summary: Mapped[str | None] = mapped_column(Text)
    error: Mapped[str | None] = mapped_column(Text)
    metadata_json: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)

    agent_run: Mapped[AgentRun] = relationship(back_populates="steps")
    events: Mapped[list[AgentEvent]] = relationship(back_populates="agent_step", cascade="all, delete-orphan")


class AgentEvent(Base):
    __tablename__ = "agent_events"
    __table_args__ = (
        UniqueConstraint("agent_run_id", "event_seq", name="uq_agent_event_run_seq"),
        Index("ix_agent_event_run_seq", "agent_run_id", "event_seq"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid_str)
    agent_run_id: Mapped[str] = mapped_column(ForeignKey("agent_runs.id", ondelete="CASCADE"), index=True, nullable=False)
    agent_step_id: Mapped[str | None] = mapped_column(ForeignKey("agent_steps.id", ondelete="CASCADE"), index=True)
    event_seq: Mapped[int] = mapped_column(Integer, nullable=False)
    agent_name: Mapped[str] = mapped_column(String(140), nullable=False)
    status: Mapped[str] = mapped_column(String(40), index=True, nullable=False)
    message: Mapped[str | None] = mapped_column(Text)
    metadata_json: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, index=True, nullable=False)

    agent_run: Mapped[AgentRun] = relationship(back_populates="events")
    agent_step: Mapped[AgentStep | None] = relationship(back_populates="events")


class AuditEvent(Base):
    __tablename__ = "audit_events"
    __table_args__ = (Index("ix_audit_object", "object_type", "object_id"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid_str)
    actor: Mapped[str] = mapped_column(String(180), index=True, nullable=False)
    action: Mapped[str] = mapped_column(String(160), index=True, nullable=False)
    object_type: Mapped[str] = mapped_column(String(100), nullable=False)
    object_id: Mapped[str] = mapped_column(String(36), nullable=False)
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, index=True, nullable=False)
    metadata_json: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)

class DocumentChunk(Base):
    __tablename__ = "document_chunks"
    __table_args__ = (
        UniqueConstraint("document_id", "chunk_index", name="uq_document_chunk_index"),
        Index("ix_document_chunk_document", "document_id"),
        Index("ix_document_chunk_hash", "chunk_hash"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid_str)
    document_id: Mapped[str] = mapped_column(ForeignKey("evidence_documents.id", ondelete="CASCADE"), nullable=False)
    chunk_index: Mapped[int] = mapped_column(Integer, nullable=False)
    text: Mapped[str] = mapped_column(Text, nullable=False)
    start_char: Mapped[int] = mapped_column(Integer, nullable=False)
    end_char: Mapped[int] = mapped_column(Integer, nullable=False)
    chunk_hash: Mapped[str] = mapped_column(String(128), nullable=False)
    embedding_vector: Mapped[str] = mapped_column(EmbeddingVectorType(384), nullable=False)
    embedding_provider: Mapped[str] = mapped_column(String(80), nullable=False)
    embedding_model: Mapped[str] = mapped_column(String(180), nullable=False)
    embedding_dimensions: Mapped[int] = mapped_column(Integer, nullable=False)
    embedding_degraded: Mapped[bool] = mapped_column(default=False, nullable=False)
    metadata_json: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)


# --- M09-M20 integrated persistence models ---
class AnalysisEvidenceHit(Base):
    __tablename__ = "analysis_evidence_hits"
    __table_args__ = (
        UniqueConstraint("agent_run_id", "chunk_id", name="uq_analysis_evidence_run_chunk"),
        Index("ix_analysis_evidence_run_rank", "agent_run_id", "rank"),
    )
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid_str)
    agent_run_id: Mapped[str] = mapped_column(ForeignKey("agent_runs.id", ondelete="CASCADE"), index=True, nullable=False)
    issue_id: Mapped[str] = mapped_column(ForeignKey("support_issues.id", ondelete="CASCADE"), index=True, nullable=False)
    document_id: Mapped[str] = mapped_column(ForeignKey("evidence_documents.id", ondelete="CASCADE"), index=True, nullable=False)
    chunk_id: Mapped[str] = mapped_column(ForeignKey("document_chunks.id", ondelete="CASCADE"), index=True, nullable=False)
    rank: Mapped[int] = mapped_column(Integer, nullable=False)
    matched_queries_json: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)
    base_score: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    query_coverage_bonus: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    issue_link_boost: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    final_score: Mapped[float] = mapped_column(Float, default=0.0, index=True, nullable=False)
    semantic_score: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    keyword_score: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    metadata_score: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    citation: Mapped[str] = mapped_column(Text, nullable=False)
    excerpt: Mapped[str] = mapped_column(Text, nullable=False)
    embedding_model: Mapped[str | None] = mapped_column(String(180))
    embedding_degraded: Mapped[bool] = mapped_column(default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)


class AnalysisImpactAssessment(Base):
    __tablename__ = "analysis_impact_assessments"
    __table_args__ = (
        UniqueConstraint("agent_run_id", "implementation_id", name="uq_impact_run_implementation"),
        Index("ix_impact_run_score", "agent_run_id", "impact_score"),
    )
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid_str)
    agent_run_id: Mapped[str] = mapped_column(ForeignKey("agent_runs.id", ondelete="CASCADE"), index=True, nullable=False)
    issue_id: Mapped[str] = mapped_column(ForeignKey("support_issues.id", ondelete="CASCADE"), index=True, nullable=False)
    implementation_id: Mapped[str] = mapped_column(ForeignKey("implementations.id", ondelete="CASCADE"), index=True, nullable=False)
    method_version_id: Mapped[str | None] = mapped_column(ForeignKey("method_versions.id", ondelete="SET NULL"), index=True)
    impact_score: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    impact_band: Mapped[str] = mapped_column(String(40), index=True, nullable=False)
    reported_source: Mapped[bool] = mapped_column(default=False, nullable=False)
    signals_json: Mapped[dict[str, float]] = mapped_column(JSON, default=dict, nullable=False)
    weights_json: Mapped[dict[str, float]] = mapped_column(JSON, default=dict, nullable=False)
    explanation_json: Mapped[list[dict[str, Any]]] = mapped_column(JSON, default=list, nullable=False)
    evidence_refs_json: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)


class InvestigationDetail(Base):
    __tablename__ = "investigation_details"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid_str)
    investigation_id: Mapped[str] = mapped_column(ForeignKey("investigations.id", ondelete="CASCADE"), unique=True, index=True, nullable=False)
    agent_run_id: Mapped[str | None] = mapped_column(ForeignKey("agent_runs.id", ondelete="SET NULL"), index=True)
    finding_id: Mapped[str | None] = mapped_column(ForeignKey("findings.id", ondelete="SET NULL"), index=True)
    qwen_run_id: Mapped[str | None] = mapped_column(String(140), index=True)
    configured_model: Mapped[str | None] = mapped_column(String(180))
    actual_model: Mapped[str | None] = mapped_column(String(180))
    duration_ms: Mapped[float | None] = mapped_column(Float)
    prompt_eval_count: Mapped[int | None] = mapped_column(Integer)
    eval_count: Mapped[int | None] = mapped_column(Integer)
    evidence_observations_json: Mapped[list[dict[str, Any]]] = mapped_column(JSON, default=list, nullable=False)
    missing_evidence_json: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)
    model_output_json: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)
    evidence_validation_status: Mapped[str] = mapped_column(String(80), default="PENDING", index=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)


class MethodVersionLineage(Base):
    __tablename__ = "method_version_lineage"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid_str)
    source_method_version_id: Mapped[str] = mapped_column(ForeignKey("method_versions.id", ondelete="CASCADE"), index=True, nullable=False)
    proposed_method_version_id: Mapped[str] = mapped_column(ForeignKey("method_versions.id", ondelete="CASCADE"), unique=True, index=True, nullable=False)
    correction_input: Mapped[str] = mapped_column(Text, nullable=False)
    author: Mapped[str] = mapped_column(String(180), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)


class LearningProposalDetail(Base):
    __tablename__ = "learning_proposal_details"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid_str)
    learning_id: Mapped[str] = mapped_column(ForeignKey("learning_proposals.id", ondelete="CASCADE"), unique=True, index=True, nullable=False)
    agent_run_id: Mapped[str | None] = mapped_column(ForeignKey("agent_runs.id", ondelete="SET NULL"), index=True)
    source_method_version_id: Mapped[str] = mapped_column(ForeignKey("method_versions.id", ondelete="CASCADE"), index=True, nullable=False)
    title: Mapped[str] = mapped_column(String(300), nullable=False)
    correction_input: Mapped[str] = mapped_column(Text, nullable=False)
    applicability: Mapped[str] = mapped_column(Text, default="", nullable=False)
    guardrails_json: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)
    validation_steps_json: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)
    qwen_run_id: Mapped[str | None] = mapped_column(String(140), index=True)
    configured_model: Mapped[str | None] = mapped_column(String(180))
    actual_model: Mapped[str | None] = mapped_column(String(180))
    duration_ms: Mapped[float | None] = mapped_column(Float)
    prompt_eval_count: Mapped[int | None] = mapped_column(Integer)
    eval_count: Mapped[int | None] = mapped_column(Integer)
    model_output_json: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)
    human_edited_by: Mapped[str | None] = mapped_column(String(180))
    human_edited_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    decision_by: Mapped[str | None] = mapped_column(String(180))
    decision_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    decision_reason: Mapped[str | None] = mapped_column(Text)


class AdoptionReceiptDetail(Base):
    __tablename__ = "adoption_receipt_details"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid_str)
    receipt_id: Mapped[str] = mapped_column(ForeignKey("adoption_receipts.id", ondelete="CASCADE"), unique=True, index=True, nullable=False)
    source_issue_id: Mapped[str] = mapped_column(ForeignKey("support_issues.id", ondelete="CASCADE"), index=True, nullable=False)
    source_method_version_id: Mapped[str] = mapped_column(ForeignKey("method_versions.id", ondelete="CASCADE"), index=True, nullable=False)
    adopted_method_version_id: Mapped[str] = mapped_column(ForeignKey("method_versions.id", ondelete="CASCADE"), index=True, nullable=False)
    approval_reason: Mapped[str] = mapped_column(Text, nullable=False)
    evidence_refs_json: Mapped[list[dict[str, Any]]] = mapped_column(JSON, default=list, nullable=False)
    receipt_payload_json: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)
    attestation_statement: Mapped[str] = mapped_column(Text, nullable=False)
    receipt_version: Mapped[str] = mapped_column(String(40), default="1.0", nullable=False)
    hash_algorithm: Mapped[str] = mapped_column(String(40), default="SHA-256", nullable=False)


class RecallNoticeDetail(Base):
    __tablename__ = "recall_notice_details"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid_str)
    recall_notice_id: Mapped[str] = mapped_column(ForeignKey("recall_notices.id", ondelete="CASCADE"), unique=True, index=True, nullable=False)
    source_issue_id: Mapped[str] = mapped_column(ForeignKey("support_issues.id", ondelete="CASCADE"), index=True, nullable=False)
    recall_run_id: Mapped[str | None] = mapped_column(ForeignKey("agent_runs.id", ondelete="SET NULL"), index=True)
    evidence_refs_json: Mapped[list[dict[str, Any]]] = mapped_column(JSON, default=list, nullable=False)
    affected_implementation_ids_json: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)
    notice_payload_json: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)
    attestation_statement: Mapped[str] = mapped_column(Text, nullable=False)
    notice_version: Mapped[str] = mapped_column(String(40), default="1.0", nullable=False)
    hash_algorithm: Mapped[str] = mapped_column(String(40), default="SHA-256", nullable=False)


class RecallCase(Base, TimestampMixin):
    __tablename__ = "recall_cases"
    __table_args__ = (UniqueConstraint("recall_notice_id", "implementation_id", name="uq_recall_implementation"),)
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid_str)
    recall_notice_id: Mapped[str] = mapped_column(ForeignKey("recall_notices.id", ondelete="CASCADE"), index=True, nullable=False)
    implementation_id: Mapped[str] = mapped_column(ForeignKey("implementations.id", ondelete="CASCADE"), index=True, nullable=False)
    dependency_edge_id: Mapped[str | None] = mapped_column(ForeignKey("dependency_edges.id", ondelete="SET NULL"), index=True)
    investigation_id: Mapped[str | None] = mapped_column(ForeignKey("investigations.id", ondelete="SET NULL"), index=True)
    status: Mapped[str] = mapped_column(String(40), default="QUEUED", index=True, nullable=False)
