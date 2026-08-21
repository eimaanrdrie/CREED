from __future__ import annotations

from typing import TypeVar

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.db.base import Base
from app.domain.models import (
    AgentRun,
    AgentStep,
    AuditEvent,
    Client,
    DeliveryMethod,
    DependencyEdge,
    EvidenceDocument,
    Finding,
    HumanDecision,
    HumanAuthority,
    Implementation,
    ImplementationDeployment,
    Investigation,
    LearningProposal,
    MethodVersion,
    Module,
    Product,
    RecallNotice,
    ResponsibilityAssignment,
    SupportIssue,
)

ModelT = TypeVar("ModelT", bound=Base)


class DomainRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def add(self, entity: ModelT) -> ModelT:
        self.session.add(entity)
        self.session.flush()
        return entity

    def get(self, model: type[ModelT], entity_id: str) -> ModelT | None:
        return self.session.get(model, entity_id)

    def list(self, model: type[ModelT], *, limit: int = 100, offset: int = 0) -> list[ModelT]:
        stmt = select(model).offset(offset).limit(limit)
        return list(self.session.scalars(stmt))

    def count(self, model: type[ModelT]) -> int:
        stmt = select(func.count()).select_from(model)
        return int(self.session.scalar(stmt) or 0)

    def get_client_by_name(self, name: str) -> Client | None:
        return self.session.scalar(select(Client).where(Client.name == name))


    def get_human_authority_by_principal(self, principal: str) -> HumanAuthority | None:
        return self.session.scalar(select(HumanAuthority).where(HumanAuthority.principal == principal))

    def list_human_authorities(self) -> list[HumanAuthority]:
        stmt = select(HumanAuthority).order_by(HumanAuthority.display_name, HumanAuthority.principal)
        return list(self.session.scalars(stmt))

    def list_responsibility_assignments(self) -> list[ResponsibilityAssignment]:
        stmt = select(ResponsibilityAssignment).order_by(
            ResponsibilityAssignment.scope_type,
            ResponsibilityAssignment.responsibility_type,
            ResponsibilityAssignment.created_at,
        )
        return list(self.session.scalars(stmt))

    def get_responsibility_assignment(
        self, *, scope_type: str, scope_id: str, responsibility_type: str
    ) -> ResponsibilityAssignment | None:
        return self.session.scalar(
            select(ResponsibilityAssignment).where(
                ResponsibilityAssignment.scope_type == scope_type,
                ResponsibilityAssignment.scope_id == scope_id,
                ResponsibilityAssignment.responsibility_type == responsibility_type,
            )
        )

    def get_product_by_name(self, name: str) -> Product | None:
        return self.session.scalar(select(Product).where(Product.name == name))

    def list_products(self) -> list[Product]:
        stmt = select(Product).order_by(Product.name)
        return list(self.session.scalars(stmt))

    def get_module(self, product_id: str, name: str) -> Module | None:
        return self.session.scalar(select(Module).where(Module.product_id == product_id, Module.name == name))

    def list_modules(self, *, product_id: str | None = None) -> list[Module]:
        stmt = select(Module)
        if product_id:
            stmt = stmt.where(Module.product_id == product_id)
        stmt = stmt.order_by(Module.name)
        return list(self.session.scalars(stmt))

    def list_implementations(self) -> list[Implementation]:
        stmt = select(Implementation).order_by(Implementation.name)
        return list(self.session.scalars(stmt))

    def list_deployments(self) -> list[ImplementationDeployment]:
        stmt = select(ImplementationDeployment).order_by(ImplementationDeployment.deployed_at.desc(), ImplementationDeployment.created_at.desc())
        return list(self.session.scalars(stmt))

    def get_deployment_event(
        self, *, implementation_id: str, environment: str, deployed_at
    ) -> ImplementationDeployment | None:
        return self.session.scalar(
            select(ImplementationDeployment).where(
                ImplementationDeployment.implementation_id == implementation_id,
                ImplementationDeployment.environment == environment,
                ImplementationDeployment.deployed_at == deployed_at,
            )
        )

    def get_delivery_method(self, *, module_id: str, name: str) -> DeliveryMethod | None:
        return self.session.scalar(
            select(DeliveryMethod).where(
                DeliveryMethod.module_id == module_id,
                DeliveryMethod.name == name,
            )
        )

    def list_delivery_methods(self) -> list[DeliveryMethod]:
        stmt = select(DeliveryMethod).order_by(DeliveryMethod.name)
        return list(self.session.scalars(stmt))

    def get_method_version(self, *, method_id: str, version: str) -> MethodVersion | None:
        return self.session.scalar(
            select(MethodVersion).where(
                MethodVersion.method_id == method_id,
                MethodVersion.version == version,
            )
        )

    def list_method_versions(self) -> list[MethodVersion]:
        stmt = select(MethodVersion).order_by(MethodVersion.created_at.desc(), MethodVersion.version)
        return list(self.session.scalars(stmt))

    def list_method_versions_for_method(self, method_id: str) -> list[MethodVersion]:
        stmt = (
            select(MethodVersion)
            .where(MethodVersion.method_id == method_id)
            .order_by(MethodVersion.created_at.asc(), MethodVersion.version)
        )
        return list(self.session.scalars(stmt))

    def get_implementation_release(self, *, client_id: str, module_id: str, release_version: str) -> Implementation | None:
        return self.session.scalar(
            select(Implementation).where(
                Implementation.client_id == client_id,
                Implementation.module_id == module_id,
                Implementation.release_version == release_version,
            )
        )

    def list_implementation_method_dependencies(self) -> list[DependencyEdge]:
        stmt = (
            select(DependencyEdge)
            .where(
                DependencyEdge.source_type == "Implementation",
                DependencyEdge.target_type == "MethodVersion",
                DependencyEdge.relationship == "USES_METHOD_VERSION",
            )
            .order_by(DependencyEdge.created_at.desc())
        )
        return list(self.session.scalars(stmt))

    def get_implementation_method_dependency(
        self, *, implementation_id: str, method_version_id: str
    ) -> DependencyEdge | None:
        return self.session.scalar(
            select(DependencyEdge).where(
                DependencyEdge.source_type == "Implementation",
                DependencyEdge.source_id == implementation_id,
                DependencyEdge.target_type == "MethodVersion",
                DependencyEdge.target_id == method_version_id,
                DependencyEdge.relationship == "USES_METHOD_VERSION",
            )
        )

    def summary_counts(self) -> dict[str, int]:
        models: dict[str, type[Base]] = {
            "clients": Client,
            "human_authorities": HumanAuthority,
            "responsibilities": ResponsibilityAssignment,
            "products": Product,
            "modules": Module,
            "issues": SupportIssue,
            "documents": EvidenceDocument,
            "methods": DeliveryMethod,
            "method_versions": MethodVersion,
            "implementations": Implementation,
            "deployments": ImplementationDeployment,
            "edges": DependencyEdge,
            "investigations": Investigation,
            "findings": Finding,
            "decisions": HumanDecision,
            "learnings": LearningProposal,
            "recalls": RecallNotice,
            "agent_runs": AgentRun,
            "agent_steps": AgentStep,
            "audit_events": AuditEvent,
        }
        return {name: self.count(model) for name, model in models.items()}
