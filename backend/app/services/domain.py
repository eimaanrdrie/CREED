from __future__ import annotations

from sqlalchemy.orm import Session

from app.domain.enums import MethodVersionStatus
from app.domain.models import AuditEvent, Client, DeliveryMethod, DependencyEdge, EvidenceDocument, HumanAuthority, Implementation, ImplementationDeployment, MethodVersion, Module, Product, ResponsibilityAssignment
from app.repositories.domain import DomainRepository
from app.services.adoption_enforcement import adoption_eligibility


class DomainService:
    def __init__(self, session: Session) -> None:
        self.session = session
        self.repo = DomainRepository(session)

    def create_client(self, *, name: str, client_type: str = "BANK", actor: str = "system") -> Client:
        existing = self.repo.get_client_by_name(name)
        if existing:
            return existing
        client = self.repo.add(Client(name=name, client_type=client_type))
        self.repo.add(
            AuditEvent(
                actor=actor,
                action="CLIENT_CREATED",
                object_type="Client",
                object_id=client.id,
                metadata_json={"name": name, "client_type": client_type},
            )
        )
        return client


    def create_human_authority(
        self,
        *,
        principal: str,
        display_name: str,
        role_title: str,
        active: bool = True,
        can_submit_human_decision: bool = False,
        can_approve_learning: bool = False,
        can_authorize_recall: bool = False,
        actor: str = "system",
    ) -> HumanAuthority:
        existing = self.repo.get_human_authority_by_principal(principal)
        if existing:
            requested = (
                display_name,
                role_title,
                active,
                can_submit_human_decision,
                can_approve_learning,
                can_authorize_recall,
            )
            current = (
                existing.display_name,
                existing.role_title,
                existing.active,
                existing.can_submit_human_decision,
                existing.can_approve_learning,
                existing.can_authorize_recall,
            )
            if requested != current:
                raise ValueError("AUTHORITY_PRINCIPAL_ALREADY_EXISTS")
            return existing
        authority = self.repo.add(
            HumanAuthority(
                principal=principal,
                display_name=display_name,
                role_title=role_title,
                active=active,
                can_submit_human_decision=can_submit_human_decision,
                can_approve_learning=can_approve_learning,
                can_authorize_recall=can_authorize_recall,
            )
        )
        self.repo.add(
            AuditEvent(
                actor=actor,
                action="HUMAN_AUTHORITY_REGISTERED",
                object_type="HumanAuthority",
                object_id=authority.id,
                metadata_json={
                    "principal": principal,
                    "role_title": role_title,
                    "active": active,
                    "can_submit_human_decision": can_submit_human_decision,
                    "can_approve_learning": can_approve_learning,
                    "can_authorize_recall": can_authorize_recall,
                },
            )
        )
        return authority

    def update_human_authority(
        self,
        *,
        authority: HumanAuthority,
        display_name: str | None = None,
        role_title: str | None = None,
        active: bool | None = None,
        can_submit_human_decision: bool | None = None,
        can_approve_learning: bool | None = None,
        can_authorize_recall: bool | None = None,
        actor: str = "system",
    ) -> HumanAuthority:
        changes: dict[str, object] = {}
        updates = {
            "display_name": display_name,
            "role_title": role_title,
            "active": active,
            "can_submit_human_decision": can_submit_human_decision,
            "can_approve_learning": can_approve_learning,
            "can_authorize_recall": can_authorize_recall,
        }
        for field, value in updates.items():
            if value is not None and getattr(authority, field) != value:
                changes[field] = value
                setattr(authority, field, value)
        if changes:
            self.repo.add(
                AuditEvent(
                    actor=actor,
                    action="HUMAN_AUTHORITY_UPDATED",
                    object_type="HumanAuthority",
                    object_id=authority.id,
                    metadata_json={"changed_fields": sorted(changes), **changes},
                )
            )
            self.session.flush()
        return authority

    def assign_responsibility(
        self,
        *,
        scope_type: str,
        scope_id: str,
        responsibility_type: str,
        authority: HumanAuthority,
        team_name: str | None = None,
        actor: str = "system",
    ) -> ResponsibilityAssignment:
        existing = self.repo.get_responsibility_assignment(
            scope_type=scope_type, scope_id=scope_id, responsibility_type=responsibility_type
        )
        if existing:
            requested = (authority.id, team_name)
            current = (existing.authority_id, existing.team_name)
            if requested != current:
                raise ValueError("RESPONSIBILITY_ALREADY_ASSIGNED")
            return existing
        assignment = self.repo.add(
            ResponsibilityAssignment(
                scope_type=scope_type,
                scope_id=scope_id,
                responsibility_type=responsibility_type,
                authority_id=authority.id,
                team_name=team_name,
            )
        )
        self.repo.add(
            AuditEvent(
                actor=actor,
                action="RESPONSIBILITY_ASSIGNED",
                object_type="ResponsibilityAssignment",
                object_id=assignment.id,
                metadata_json={
                    "scope_type": scope_type,
                    "scope_id": scope_id,
                    "responsibility_type": responsibility_type,
                    "authority_id": authority.id,
                    "principal": authority.principal,
                    "team_name": team_name,
                },
            )
        )
        return assignment

    def reassign_responsibility(
        self,
        *,
        assignment: ResponsibilityAssignment,
        authority: HumanAuthority,
        team_name: str | None,
        reason: str,
        actor: str = "system",
    ) -> ResponsibilityAssignment:
        previous = {
            "authority_id": assignment.authority_id,
            "principal": assignment.authority.principal if assignment.authority else None,
            "team_name": assignment.team_name,
        }
        if assignment.authority_id == authority.id and assignment.team_name == team_name:
            return assignment
        assignment.authority = authority
        assignment.authority_id = authority.id
        assignment.team_name = team_name
        self.session.flush()
        self.repo.add(
            AuditEvent(
                actor=actor,
                action="RESPONSIBILITY_REASSIGNED",
                object_type="ResponsibilityAssignment",
                object_id=assignment.id,
                metadata_json={
                    "scope_type": assignment.scope_type,
                    "scope_id": assignment.scope_id,
                    "responsibility_type": assignment.responsibility_type,
                    "previous": previous,
                    "authority_id": authority.id,
                    "principal": authority.principal,
                    "team_name": team_name,
                    "reason": reason,
                },
            )
        )
        return assignment

    def remove_responsibility(
        self, *, assignment: ResponsibilityAssignment, reason: str, actor: str = "system"
    ) -> None:
        snapshot = {
            "scope_type": assignment.scope_type,
            "scope_id": assignment.scope_id,
            "responsibility_type": assignment.responsibility_type,
            "authority_id": assignment.authority_id,
            "principal": assignment.authority.principal if assignment.authority else None,
            "team_name": assignment.team_name,
            "reason": reason,
        }
        assignment_id = assignment.id
        self.session.delete(assignment)
        self.repo.add(
            AuditEvent(
                actor=actor,
                action="RESPONSIBILITY_REMOVED",
                object_type="ResponsibilityAssignment",
                object_id=assignment_id,
                metadata_json=snapshot,
            )
        )

    def create_product(
        self,
        *,
        name: str,
        description: str | None = None,
        active: bool = True,
        actor: str = "system",
    ) -> Product:
        existing = self.repo.get_product_by_name(name)
        if existing:
            requested = (description, active)
            current = (existing.description, existing.active)
            if requested != current:
                raise ValueError("PRODUCT_NAME_ALREADY_EXISTS")
            return existing
        product = self.repo.add(Product(name=name, description=description, active=active))
        self.repo.add(
            AuditEvent(
                actor=actor,
                action="PRODUCT_CREATED",
                object_type="Product",
                object_id=product.id,
                metadata_json={"name": name, "active": active},
            )
        )
        return product

    def update_product(
        self,
        *,
        product: Product,
        description: str | None = None,
        active: bool | None = None,
        actor: str = "system",
    ) -> Product:
        changes: dict[str, object] = {}
        if description is not None and product.description != description:
            changes["description"] = description
            product.description = description
        if active is not None and product.active != active:
            changes["active"] = active
            product.active = active
        if changes:
            self.repo.add(
                AuditEvent(
                    actor=actor,
                    action="PRODUCT_UPDATED",
                    object_type="Product",
                    object_id=product.id,
                    metadata_json={"changed_fields": sorted(changes), **changes},
                )
            )
            self.session.flush()
        return product

    def create_module(
        self,
        *,
        product: Product,
        name: str,
        description: str | None = None,
        active: bool = True,
        actor: str = "system",
    ) -> Module:
        existing = self.repo.get_module(product.id, name)
        if existing:
            requested = (description, active)
            current = (existing.description, existing.active)
            if requested != current:
                raise ValueError("MODULE_NAME_ALREADY_EXISTS")
            return existing
        module = self.repo.add(Module(product_id=product.id, name=name, description=description, active=active))
        self.repo.add(
            AuditEvent(
                actor=actor,
                action="MODULE_CREATED",
                object_type="Module",
                object_id=module.id,
                metadata_json={"name": name, "product_id": product.id, "active": active},
            )
        )
        return module

    def update_module(
        self,
        *,
        module: Module,
        description: str | None = None,
        active: bool | None = None,
        actor: str = "system",
    ) -> Module:
        changes: dict[str, object] = {}
        if description is not None and module.description != description:
            changes["description"] = description
            module.description = description
        if active is not None and module.active != active:
            changes["active"] = active
            module.active = active
        if changes:
            self.repo.add(
                AuditEvent(
                    actor=actor,
                    action="MODULE_UPDATED",
                    object_type="Module",
                    object_id=module.id,
                    metadata_json={"changed_fields": sorted(changes), **changes},
                )
            )
            self.session.flush()
        return module

    def create_delivery_method(
        self,
        *,
        module: Module,
        name: str,
        description: str | None = None,
        actor: str = "system",
    ) -> DeliveryMethod:
        existing = self.repo.get_delivery_method(module_id=module.id, name=name)
        if existing:
            return existing
        method = self.repo.add(
            DeliveryMethod(
                module_id=module.id,
                name=name,
                description=description,
            )
        )
        self.repo.add(
            AuditEvent(
                actor=actor,
                action="DELIVERY_METHOD_CREATED",
                object_type="DeliveryMethod",
                object_id=method.id,
                metadata_json={"name": name, "module_id": module.id},
            )
        )
        return method

    def create_method_version(
        self,
        *,
        method: DeliveryMethod,
        version: str,
        summary: str | None = None,
        actor: str = "system",
    ) -> MethodVersion:
        existing = self.repo.get_method_version(method_id=method.id, version=version)
        if existing:
            return existing
        method_version = self.repo.add(
            MethodVersion(
                method_id=method.id,
                version=version,
                status=MethodVersionStatus.DRAFT.value,
                summary=summary,
            )
        )
        self.repo.add(
            AuditEvent(
                actor=actor,
                action="METHOD_VERSION_DRAFT_CREATED",
                object_type="MethodVersion",
                object_id=method_version.id,
                metadata_json={
                    "method_id": method.id,
                    "version": version,
                    "status": MethodVersionStatus.DRAFT.value,
                },
            )
        )
        return method_version

    def approve_baseline_method_version(
        self,
        *,
        method_version: MethodVersion,
        authority: HumanAuthority,
        reason: str,
    ) -> MethodVersion:
        if method_version.status != MethodVersionStatus.DRAFT.value:
            raise ValueError("METHOD_VERSION_NOT_DRAFT")

        established_states = {MethodVersionStatus.APPROVED.value, MethodVersionStatus.REVOKED.value}
        siblings = self.repo.list_method_versions_for_method(method_version.method_id)
        if any(item.id != method_version.id and item.status in established_states for item in siblings):
            raise ValueError("METHOD_BASELINE_ALREADY_ESTABLISHED")

        method_version.status = MethodVersionStatus.APPROVED.value
        self.repo.add(
            AuditEvent(
                actor=authority.principal,
                action="BASELINE_METHOD_VERSION_APPROVED",
                object_type="MethodVersion",
                object_id=method_version.id,
                metadata_json={
                    "method_id": method_version.method_id,
                    "version": method_version.version,
                    "reason": reason,
                    "authority_id": authority.id,
                    "authority_display_name": authority.display_name,
                    "authority_role_title": authority.role_title,
                    "authority_capability": "can_approve_learning",
                    "approval_type": "INITIAL_BASELINE",
                },
            )
        )
        self.session.flush()
        return method_version


    def create_implementation(
        self,
        *,
        client: Client,
        product: Product,
        module: Module,
        name: str,
        release_version: str,
        actor: str = "system",
    ) -> Implementation:
        existing = self.repo.get_implementation_release(
            client_id=client.id,
            module_id=module.id,
            release_version=release_version,
        )
        if existing:
            return existing
        implementation = self.repo.add(
            Implementation(
                client_id=client.id,
                product_id=product.id,
                module_id=module.id,
                name=name,
                release_version=release_version,
                status="ACTIVE",
            )
        )
        self.repo.add(
            AuditEvent(
                actor=actor,
                action="IMPLEMENTATION_CREATED",
                object_type="Implementation",
                object_id=implementation.id,
                metadata_json={
                    "name": name,
                    "client_id": client.id,
                    "product_id": product.id,
                    "module_id": module.id,
                    "release_version": release_version,
                },
            )
        )
        return implementation

    def record_deployment(
        self,
        *,
        implementation: Implementation,
        environment: str,
        deployed_at,
        evidence_document: EvidenceDocument,
        deployment_reference: str | None = None,
        notes: str | None = None,
        actor: str = "system",
    ) -> ImplementationDeployment:
        existing = self.repo.get_deployment_event(
            implementation_id=implementation.id,
            environment=environment,
            deployed_at=deployed_at,
        )
        if existing:
            requested = (
                deployment_reference,
                evidence_document.id,
                notes,
            )
            current = (
                existing.deployment_reference,
                existing.evidence_document_id,
                existing.notes,
            )
            if requested != current:
                raise ValueError("DEPLOYMENT_EVENT_ALREADY_EXISTS")
            return existing

        deployment = self.repo.add(
            ImplementationDeployment(
                implementation_id=implementation.id,
                environment=environment,
                status="DEPLOYED",
                deployed_at=deployed_at,
                deployment_reference=deployment_reference,
                evidence_document_id=evidence_document.id,
                notes=notes,
            )
        )
        self.repo.add(
            AuditEvent(
                actor=actor,
                action="RELEASE_DEPLOYMENT_RECORDED",
                object_type="ImplementationDeployment",
                object_id=deployment.id,
                metadata_json={
                    "implementation_id": implementation.id,
                    "release_version": implementation.release_version,
                    "environment": environment,
                    "deployed_at": deployed_at.isoformat(),
                    "deployment_reference": deployment_reference,
                    "evidence_document_id": evidence_document.id,
                },
            )
        )
        return deployment


    def register_implementation_method_dependency(
        self,
        *,
        implementation: Implementation,
        method_version: MethodVersion,
        evidence_document: EvidenceDocument,
        actor: str = "system",
    ) -> DependencyEdge:
        if method_version.method.module_id != implementation.module_id:
            raise ValueError("IMPLEMENTATION_METHOD_MODULE_MISMATCH")
        adoption = adoption_eligibility(
            self.session,
            method_version=method_version,
            implementation=implementation,
        )
        if not adoption["allowed"]:
            raise ValueError(str(adoption["reason"]))
        existing = self.repo.get_implementation_method_dependency(
            implementation_id=implementation.id,
            method_version_id=method_version.id,
        )
        if existing:
            if existing.evidence_document_id != evidence_document.id:
                raise ValueError("DEPENDENCY_ALREADY_EXISTS_WITH_DIFFERENT_EVIDENCE")
            return existing
        edge = self.repo.add(
            DependencyEdge(
                source_type="Implementation",
                source_id=implementation.id,
                target_type="MethodVersion",
                target_id=method_version.id,
                relationship="USES_METHOD_VERSION",
                confidence=1.0,
                evidence_document_id=evidence_document.id,
            )
        )
        self.repo.add(
            AuditEvent(
                actor=actor,
                action="ABOM_DEPENDENCY_REGISTERED",
                object_type="DependencyEdge",
                object_id=edge.id,
                metadata_json={
                    "implementation_id": implementation.id,
                    "method_version_id": method_version.id,
                    "evidence_document_id": evidence_document.id,
                    "relationship": "USES_METHOD_VERSION",
                    "adoption_scope_enforced": bool(adoption["enforced"]),
                    "adoption_scope_mode": adoption.get("scope_mode"),
                    "adoption_receipt_id": adoption.get("receipt_id"),
                },
            )
        )
        return edge

    def remove_implementation_method_dependency(
        self,
        *,
        edge: DependencyEdge,
        reason: str,
        actor: str = "system",
    ) -> None:
        if not (
            edge.source_type == "Implementation"
            and edge.target_type == "MethodVersion"
            and edge.relationship == "USES_METHOD_VERSION"
        ):
            raise ValueError("NOT_IMPLEMENTATION_METHOD_DEPENDENCY")
        snapshot = {
            "implementation_id": edge.source_id,
            "method_version_id": edge.target_id,
            "evidence_document_id": edge.evidence_document_id,
            "relationship": edge.relationship,
            "reason": reason,
        }
        edge_id = edge.id
        self.session.delete(edge)
        self.repo.add(
            AuditEvent(
                actor=actor,
                action="ABOM_DEPENDENCY_REMOVED",
                object_type="DependencyEdge",
                object_id=edge_id,
                metadata_json=snapshot,
            )
        )

    def summary(self) -> dict[str, int]:
        return self.repo.summary_counts()

    def commit(self) -> None:
        self.session.commit()
