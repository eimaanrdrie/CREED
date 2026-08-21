from __future__ import annotations

from collections.abc import Generator
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, Header, HTTPException
from pydantic import BaseModel, Field, field_validator
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.domain.models import Client, DeliveryMethod, DependencyEdge, EvidenceDocument, HumanAuthority, Implementation, ImplementationDeployment, MethodVersion, Module, Product, ResponsibilityAssignment
from app.repositories.domain import DomainRepository
from app.services.authority_enforcement import AuthorityEnforcementError, require_human_authority
from app.services.domain import DomainService
from app.services.adoption_enforcement import adoption_policy_for_version

router = APIRouter(prefix="/domain", tags=["domain"])


class ClientCreate(BaseModel):
    name: str = Field(min_length=2, max_length=180)
    client_type: str = Field(default="BANK", min_length=2, max_length=80)

    @field_validator("name", "client_type")
    @classmethod
    def strip_non_empty(cls, value: str) -> str:
        cleaned = value.strip()
        if len(cleaned) < 2:
            raise ValueError("must contain at least 2 non-whitespace characters")
        return cleaned


class ClientRead(BaseModel):
    id: str
    name: str
    client_type: str




class HumanAuthorityCreate(BaseModel):
    principal: str = Field(min_length=3, max_length=180)
    display_name: str = Field(min_length=2, max_length=180)
    role_title: str = Field(min_length=2, max_length=180)
    active: bool = True
    can_submit_human_decision: bool = False
    can_approve_learning: bool = False
    can_authorize_recall: bool = False

    @field_validator("principal", "display_name", "role_title")
    @classmethod
    def strip_authority_text(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("must not be blank")
        return cleaned


class HumanAuthorityUpdate(BaseModel):
    display_name: str | None = Field(default=None, min_length=2, max_length=180)
    role_title: str | None = Field(default=None, min_length=2, max_length=180)
    active: bool | None = None
    can_submit_human_decision: bool | None = None
    can_approve_learning: bool | None = None
    can_authorize_recall: bool | None = None

    @field_validator("display_name", "role_title")
    @classmethod
    def strip_authority_optional_text(cls, value: str | None) -> str | None:
        if value is None:
            return None
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("must not be blank")
        return cleaned


class HumanAuthorityRead(BaseModel):
    id: str
    principal: str
    display_name: str
    role_title: str
    active: bool
    can_submit_human_decision: bool
    can_approve_learning: bool
    can_authorize_recall: bool
    created_at: datetime
    updated_at: datetime


RESPONSIBILITY_SCOPES = {"PRODUCT", "MODULE", "IMPLEMENTATION", "METHOD"}
RESPONSIBILITY_TYPES = {
    "PRODUCT_OWNER",
    "MODULE_OWNER",
    "TECHNICAL_OWNER",
    "QA_OWNER",
    "IMPLEMENTATION_LEAD",
}
RESPONSIBILITY_ALLOWED: dict[str, set[str]] = {
    "PRODUCT": {"PRODUCT_OWNER", "QA_OWNER"},
    "MODULE": {"MODULE_OWNER", "TECHNICAL_OWNER", "QA_OWNER"},
    "IMPLEMENTATION": {"IMPLEMENTATION_LEAD", "TECHNICAL_OWNER", "QA_OWNER"},
    "METHOD": {"TECHNICAL_OWNER", "QA_OWNER"},
}


class ResponsibilityAssignmentCreate(BaseModel):
    scope_type: str = Field(min_length=3, max_length=40)
    scope_id: str = Field(min_length=1, max_length=36)
    responsibility_type: str = Field(min_length=3, max_length=60)
    authority_id: str = Field(min_length=1, max_length=36)
    team_name: str | None = Field(default=None, max_length=180)

    @field_validator("scope_type")
    @classmethod
    def validate_scope_type(cls, value: str) -> str:
        cleaned = value.strip().upper()
        if cleaned not in RESPONSIBILITY_SCOPES:
            raise ValueError("unsupported responsibility scope")
        return cleaned

    @field_validator("responsibility_type")
    @classmethod
    def validate_responsibility_type(cls, value: str) -> str:
        cleaned = value.strip().upper()
        if cleaned not in RESPONSIBILITY_TYPES:
            raise ValueError("unsupported responsibility type")
        return cleaned

    @field_validator("scope_id", "authority_id")
    @classmethod
    def strip_assignment_ids(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("must not be blank")
        return cleaned

    @field_validator("team_name")
    @classmethod
    def strip_team_name(cls, value: str | None) -> str | None:
        if value is None:
            return None
        cleaned = value.strip()
        return cleaned or None


class ResponsibilityAssignmentUpdate(BaseModel):
    authority_id: str = Field(min_length=1, max_length=36)
    team_name: str | None = Field(default=None, max_length=180)
    reason: str = Field(min_length=3, max_length=2000)

    @field_validator("authority_id")
    @classmethod
    def strip_update_authority(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("must not be blank")
        return cleaned

    @field_validator("team_name")
    @classmethod
    def strip_update_team(cls, value: str | None) -> str | None:
        if value is None:
            return None
        cleaned = value.strip()
        return cleaned or None

    @field_validator("reason")
    @classmethod
    def strip_update_reason(cls, value: str) -> str:
        cleaned = value.strip()
        if len(cleaned) < 3:
            raise ValueError("reason must contain at least 3 non-whitespace characters")
        return cleaned


class ResponsibilityAssignmentRemove(BaseModel):
    reason: str = Field(min_length=3, max_length=2000)

    @field_validator("reason")
    @classmethod
    def strip_remove_reason(cls, value: str) -> str:
        cleaned = value.strip()
        if len(cleaned) < 3:
            raise ValueError("reason must contain at least 3 non-whitespace characters")
        return cleaned


class ResponsibilityAssignmentRead(BaseModel):
    id: str
    scope_type: str
    scope_id: str
    scope_name: str
    scope_context: str
    responsibility_type: str
    authority_id: str
    principal: str
    display_name: str
    authority_role_title: str
    authority_active: bool
    team_name: str | None = None
    created_at: datetime
    updated_at: datetime


class ProductCreate(BaseModel):
    name: str = Field(min_length=2, max_length=180)
    description: str | None = Field(default=None, max_length=3000)
    active: bool = True

    @field_validator("name")
    @classmethod
    def strip_product_name(cls, value: str) -> str:
        cleaned = value.strip()
        if len(cleaned) < 2:
            raise ValueError("must contain at least 2 non-whitespace characters")
        return cleaned

    @field_validator("description")
    @classmethod
    def strip_product_description(cls, value: str | None) -> str | None:
        if value is None:
            return None
        cleaned = value.strip()
        return cleaned or None


class ProductUpdate(BaseModel):
    description: str | None = Field(default=None, max_length=3000)
    active: bool | None = None

    @field_validator("description")
    @classmethod
    def strip_product_update_description(cls, value: str | None) -> str | None:
        if value is None:
            return None
        cleaned = value.strip()
        return cleaned or None


class ProductRead(BaseModel):
    id: str
    name: str
    description: str | None = None
    active: bool


class ModuleCreate(BaseModel):
    product_id: str = Field(min_length=1, max_length=36)
    name: str = Field(min_length=2, max_length=180)
    description: str | None = Field(default=None, max_length=3000)
    active: bool = True

    @field_validator("product_id")
    @classmethod
    def strip_module_product_id(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("must not be blank")
        return cleaned

    @field_validator("name")
    @classmethod
    def strip_module_name(cls, value: str) -> str:
        cleaned = value.strip()
        if len(cleaned) < 2:
            raise ValueError("must contain at least 2 non-whitespace characters")
        return cleaned

    @field_validator("description")
    @classmethod
    def strip_module_description(cls, value: str | None) -> str | None:
        if value is None:
            return None
        cleaned = value.strip()
        return cleaned or None


class ModuleUpdate(BaseModel):
    description: str | None = Field(default=None, max_length=3000)
    active: bool | None = None

    @field_validator("description")
    @classmethod
    def strip_module_update_description(cls, value: str | None) -> str | None:
        if value is None:
            return None
        cleaned = value.strip()
        return cleaned or None


class ModuleRead(BaseModel):
    id: str
    product_id: str
    name: str
    description: str | None = None
    active: bool


class DeliveryMethodCreate(BaseModel):
    module_id: str = Field(min_length=1, max_length=36)
    name: str = Field(min_length=2, max_length=220)
    description: str | None = Field(default=None, max_length=3000)

    @field_validator("module_id", "name")
    @classmethod
    def strip_required(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("must not be blank")
        return cleaned

    @field_validator("description")
    @classmethod
    def strip_optional(cls, value: str | None) -> str | None:
        if value is None:
            return None
        cleaned = value.strip()
        return cleaned or None


class DeliveryMethodRead(BaseModel):
    id: str
    product_id: str
    product_name: str
    module_id: str
    module_name: str
    name: str
    description: str | None = None


class MethodVersionCreate(BaseModel):
    method_id: str = Field(min_length=1, max_length=36)
    version: str = Field(min_length=1, max_length=80)
    summary: str | None = Field(default=None, max_length=5000)

    @field_validator("method_id", "version")
    @classmethod
    def strip_required(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("must not be blank")
        return cleaned

    @field_validator("summary")
    @classmethod
    def strip_optional(cls, value: str | None) -> str | None:
        if value is None:
            return None
        cleaned = value.strip()
        return cleaned or None


class MethodVersionRead(BaseModel):
    id: str
    method_id: str
    method_name: str
    product_id: str
    product_name: str
    module_id: str
    module_name: str
    version: str
    status: str
    summary: str | None = None
    revoked_at: datetime | None = None
    adoption_policy: dict | None = None


class MethodVersionBaselineApproval(BaseModel):
    reviewer: str = Field(min_length=3, max_length=180)
    reason: str = Field(min_length=3, max_length=3000)

    @field_validator("reviewer", "reason")
    @classmethod
    def strip_baseline_approval_text(cls, value: str) -> str:
        cleaned = value.strip()
        if len(cleaned) < 3:
            raise ValueError("must contain at least 3 non-whitespace characters")
        return cleaned


class ImplementationCreate(BaseModel):
    client_id: str = Field(min_length=1, max_length=36)
    product_id: str = Field(min_length=1, max_length=36)
    module_id: str = Field(min_length=1, max_length=36)
    name: str = Field(min_length=2, max_length=220)
    release_version: str = Field(min_length=1, max_length=80)

    @field_validator("client_id", "product_id", "module_id", "name", "release_version")
    @classmethod
    def strip_required(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("must not be blank")
        return cleaned


class ImplementationRead(BaseModel):
    id: str
    client_id: str
    client_name: str
    product_id: str
    product_name: str
    module_id: str
    module_name: str
    name: str
    release_version: str
    status: str


class DeploymentCreate(BaseModel):
    implementation_id: str = Field(min_length=1, max_length=36)
    environment: str = Field(min_length=2, max_length=40)
    deployed_at: datetime
    deployment_reference: str | None = Field(default=None, max_length=140)
    evidence_document_id: str = Field(min_length=1, max_length=36)
    notes: str | None = Field(default=None, max_length=4000)

    @field_validator("implementation_id", "evidence_document_id")
    @classmethod
    def strip_deployment_ids(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("must not be blank")
        return cleaned

    @field_validator("environment")
    @classmethod
    def validate_environment(cls, value: str) -> str:
        cleaned = value.strip().upper()
        allowed = {"DEVELOPMENT", "SIT", "UAT", "PRODUCTION", "DR"}
        if cleaned not in allowed:
            raise ValueError(f"environment must be one of {', '.join(sorted(allowed))}")
        return cleaned

    @field_validator("deployment_reference", "notes")
    @classmethod
    def strip_optional_deployment_text(cls, value: str | None) -> str | None:
        if value is None:
            return None
        cleaned = value.strip()
        return cleaned or None


class DeploymentRead(BaseModel):
    id: str
    implementation_id: str
    implementation_name: str
    implementation_status: str
    client_id: str
    client_name: str
    product_id: str
    product_name: str
    module_id: str
    module_name: str
    release_version: str
    environment: str
    status: str
    deployed_at: datetime
    deployment_reference: str | None = None
    evidence_document_id: str | None = None
    evidence_title: str | None = None
    evidence_document_type: str | None = None
    evidence_content_hash: str | None = None
    notes: str | None = None
    created_at: datetime
    updated_at: datetime


class ImplementationMethodDependencyCreate(BaseModel):
    implementation_id: str = Field(min_length=1, max_length=36)
    method_version_id: str = Field(min_length=1, max_length=36)
    evidence_document_id: str = Field(min_length=1, max_length=36)

    @field_validator("implementation_id", "method_version_id", "evidence_document_id")
    @classmethod
    def strip_dependency_ids(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("must not be blank")
        return cleaned


class ImplementationMethodDependencyRemove(BaseModel):
    reason: str = Field(min_length=3, max_length=2000)

    @field_validator("reason")
    @classmethod
    def strip_reason(cls, value: str) -> str:
        cleaned = value.strip()
        if len(cleaned) < 3:
            raise ValueError("reason must contain at least 3 non-whitespace characters")
        return cleaned


class ImplementationMethodDependencyRead(BaseModel):
    id: str
    relationship: str
    implementation_id: str
    implementation_name: str
    implementation_release_version: str
    implementation_status: str
    client_id: str
    client_name: str
    product_id: str
    product_name: str
    module_id: str
    module_name: str
    method_id: str
    method_name: str
    method_version_id: str
    method_version: str
    method_version_status: str
    evidence_document_id: str | None = None
    evidence_title: str | None = None
    evidence_document_type: str | None = None
    evidence_version: str | None = None
    evidence_content_hash: str | None = None
    created_at: datetime


class DomainSummary(BaseModel):
    counts: dict[str, int]


def get_domain_db() -> Generator[Session, None, None]:
    try:
        yield from get_db()
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail="DATABASE_NOT_CONFIGURED") from exc




def _human_authority_read(item: HumanAuthority) -> HumanAuthorityRead:
    return HumanAuthorityRead(
        id=item.id,
        principal=item.principal,
        display_name=item.display_name,
        role_title=item.role_title,
        active=item.active,
        can_submit_human_decision=item.can_submit_human_decision,
        can_approve_learning=item.can_approve_learning,
        can_authorize_recall=item.can_authorize_recall,
        created_at=item.created_at if item.created_at.tzinfo is not None else item.created_at.replace(tzinfo=timezone.utc),
        updated_at=item.updated_at if item.updated_at.tzinfo is not None else item.updated_at.replace(tzinfo=timezone.utc),
    )


def _responsibility_scope(item: ResponsibilityAssignment, db: Session) -> tuple[str, str]:
    if item.scope_type == "PRODUCT":
        target = db.get(Product, item.scope_id)
        if target is None:
            raise HTTPException(status_code=409, detail="DANGLING_RESPONSIBILITY_SCOPE")
        return target.name, "Product"
    if item.scope_type == "MODULE":
        target = db.get(Module, item.scope_id)
        if target is None:
            raise HTTPException(status_code=409, detail="DANGLING_RESPONSIBILITY_SCOPE")
        return target.name, f"{target.product.name} / {target.name}"
    if item.scope_type == "IMPLEMENTATION":
        target = db.get(Implementation, item.scope_id)
        if target is None:
            raise HTTPException(status_code=409, detail="DANGLING_RESPONSIBILITY_SCOPE")
        return target.name, f"{target.client.name} · {target.product.name} / {target.module.name} · {target.release_version}"
    if item.scope_type == "METHOD":
        target = db.get(DeliveryMethod, item.scope_id)
        if target is None:
            raise HTTPException(status_code=409, detail="DANGLING_RESPONSIBILITY_SCOPE")
        return target.name, f"{target.module.product.name} / {target.module.name}"
    raise HTTPException(status_code=409, detail="UNKNOWN_RESPONSIBILITY_SCOPE")


def _responsibility_read(item: ResponsibilityAssignment, db: Session) -> ResponsibilityAssignmentRead:
    scope_name, scope_context = _responsibility_scope(item, db)
    authority = item.authority
    created_at = item.created_at if item.created_at.tzinfo is not None else item.created_at.replace(tzinfo=timezone.utc)
    updated_at = item.updated_at if item.updated_at.tzinfo is not None else item.updated_at.replace(tzinfo=timezone.utc)
    return ResponsibilityAssignmentRead(
        id=item.id,
        scope_type=item.scope_type,
        scope_id=item.scope_id,
        scope_name=scope_name,
        scope_context=scope_context,
        responsibility_type=item.responsibility_type,
        authority_id=authority.id,
        principal=authority.principal,
        display_name=authority.display_name,
        authority_role_title=authority.role_title,
        authority_active=authority.active,
        team_name=item.team_name,
        created_at=created_at,
        updated_at=updated_at,
    )


def _get_responsibility_scope(db: Session, scope_type: str, scope_id: str):
    model_map = {
        "PRODUCT": Product,
        "MODULE": Module,
        "IMPLEMENTATION": Implementation,
        "METHOD": DeliveryMethod,
    }
    model = model_map[scope_type]
    target = db.get(model, scope_id)
    if target is None:
        raise HTTPException(status_code=404, detail="RESPONSIBILITY_SCOPE_NOT_FOUND")
    return target


def _delivery_method_read(item: DeliveryMethod) -> DeliveryMethodRead:
    module = item.module
    product = module.product
    return DeliveryMethodRead(
        id=item.id,
        product_id=product.id,
        product_name=product.name,
        module_id=module.id,
        module_name=module.name,
        name=item.name,
        description=item.description,
    )


def _method_version_read(item: MethodVersion, db: Session) -> MethodVersionRead:
    method = item.method
    module = method.module
    product = module.product
    return MethodVersionRead(
        id=item.id,
        method_id=method.id,
        method_name=method.name,
        product_id=product.id,
        product_name=product.name,
        module_id=module.id,
        module_name=module.name,
        version=item.version,
        status=item.status,
        summary=item.summary,
        revoked_at=item.revoked_at,
        adoption_policy=adoption_policy_for_version(db, item.id),
    )


def _implementation_read(item: Implementation) -> ImplementationRead:
    return ImplementationRead(
        id=item.id,
        client_id=item.client_id,
        client_name=item.client.name,
        product_id=item.product_id,
        product_name=item.product.name,
        module_id=item.module_id,
        module_name=item.module.name,
        name=item.name,
        release_version=item.release_version,
        status=item.status,
    )


def _deployment_read(item: ImplementationDeployment) -> DeploymentRead:
    implementation = item.implementation
    evidence = item.evidence_document
    deployed_at = item.deployed_at if item.deployed_at.tzinfo is not None else item.deployed_at.replace(tzinfo=timezone.utc)
    created_at = item.created_at if item.created_at.tzinfo is not None else item.created_at.replace(tzinfo=timezone.utc)
    updated_at = item.updated_at if item.updated_at.tzinfo is not None else item.updated_at.replace(tzinfo=timezone.utc)
    return DeploymentRead(
        id=item.id,
        implementation_id=implementation.id,
        implementation_name=implementation.name,
        implementation_status=implementation.status,
        client_id=implementation.client_id,
        client_name=implementation.client.name,
        product_id=implementation.product_id,
        product_name=implementation.product.name,
        module_id=implementation.module_id,
        module_name=implementation.module.name,
        release_version=implementation.release_version,
        environment=item.environment,
        status=item.status,
        deployed_at=deployed_at,
        deployment_reference=item.deployment_reference,
        evidence_document_id=evidence.id if evidence else None,
        evidence_title=evidence.title if evidence else None,
        evidence_document_type=evidence.document_type if evidence else None,
        evidence_content_hash=evidence.content_hash if evidence else None,
        notes=item.notes,
        created_at=created_at,
        updated_at=updated_at,
    )


def _implementation_method_dependency_read(
    item: DependencyEdge, db: Session
) -> ImplementationMethodDependencyRead:
    implementation = db.get(Implementation, item.source_id)
    method_version = db.get(MethodVersion, item.target_id)
    if implementation is None or method_version is None:
        raise HTTPException(status_code=409, detail="DANGLING_ABOM_DEPENDENCY")
    method = method_version.method
    module = method.module
    product = module.product
    evidence = db.get(EvidenceDocument, item.evidence_document_id) if item.evidence_document_id else None
    return ImplementationMethodDependencyRead(
        id=item.id,
        relationship=item.relationship,
        implementation_id=implementation.id,
        implementation_name=implementation.name,
        implementation_release_version=implementation.release_version,
        implementation_status=implementation.status,
        client_id=implementation.client_id,
        client_name=implementation.client.name,
        product_id=product.id,
        product_name=product.name,
        module_id=module.id,
        module_name=module.name,
        method_id=method.id,
        method_name=method.name,
        method_version_id=method_version.id,
        method_version=method_version.version,
        method_version_status=method_version.status,
        evidence_document_id=evidence.id if evidence else None,
        evidence_title=evidence.title if evidence else None,
        evidence_document_type=evidence.document_type if evidence else None,
        evidence_version=evidence.version if evidence else None,
        evidence_content_hash=evidence.content_hash if evidence else None,
        created_at=item.created_at if item.created_at.tzinfo is not None else item.created_at.replace(tzinfo=timezone.utc),
    )


@router.get("/summary", response_model=DomainSummary)
def domain_summary(db: Session = Depends(get_domain_db)) -> DomainSummary:
    try:
        return DomainSummary(counts=DomainService(db).summary())
    except SQLAlchemyError as exc:
        raise HTTPException(status_code=503, detail=f"DATABASE_UNAVAILABLE: {exc.__class__.__name__}") from exc


@router.get("/clients", response_model=list[ClientRead])
def list_clients(db: Session = Depends(get_domain_db)) -> list[ClientRead]:
    try:
        clients = DomainRepository(db).list(Client)
        return [ClientRead(id=item.id, name=item.name, client_type=item.client_type) for item in clients]
    except SQLAlchemyError as exc:
        raise HTTPException(status_code=503, detail=f"DATABASE_UNAVAILABLE: {exc.__class__.__name__}") from exc


@router.post("/clients", response_model=ClientRead, status_code=201)
def create_client(payload: ClientCreate, db: Session = Depends(get_domain_db)) -> ClientRead:
    try:
        service = DomainService(db)
        client = service.create_client(
            name=payload.name,
            client_type=payload.client_type,
            actor="api-user",
        )
        service.commit()
        return ClientRead(id=client.id, name=client.name, client_type=client.client_type)
    except SQLAlchemyError as exc:
        db.rollback()
        raise HTTPException(status_code=503, detail=f"DATABASE_UNAVAILABLE: {exc.__class__.__name__}") from exc




@router.get("/authorities", response_model=list[HumanAuthorityRead])
def list_human_authorities(db: Session = Depends(get_domain_db)) -> list[HumanAuthorityRead]:
    try:
        return [_human_authority_read(item) for item in DomainRepository(db).list_human_authorities()]
    except SQLAlchemyError as exc:
        raise HTTPException(status_code=503, detail=f"DATABASE_UNAVAILABLE: {exc.__class__.__name__}") from exc


@router.post("/authorities", response_model=HumanAuthorityRead, status_code=201)
def create_human_authority(payload: HumanAuthorityCreate, db: Session = Depends(get_domain_db)) -> HumanAuthorityRead:
    try:
        service = DomainService(db)
        try:
            authority = service.create_human_authority(
                principal=payload.principal,
                display_name=payload.display_name,
                role_title=payload.role_title,
                active=payload.active,
                can_submit_human_decision=payload.can_submit_human_decision,
                can_approve_learning=payload.can_approve_learning,
                can_authorize_recall=payload.can_authorize_recall,
                actor="api-user",
            )
        except ValueError as exc:
            if str(exc) == "AUTHORITY_PRINCIPAL_ALREADY_EXISTS":
                raise HTTPException(status_code=409, detail=str(exc)) from exc
            raise
        service.commit()
        return _human_authority_read(authority)
    except HTTPException:
        db.rollback()
        raise
    except SQLAlchemyError as exc:
        db.rollback()
        raise HTTPException(status_code=503, detail=f"DATABASE_UNAVAILABLE: {exc.__class__.__name__}") from exc


@router.patch("/authorities/{authority_id}", response_model=HumanAuthorityRead)
def update_human_authority(
    authority_id: str, payload: HumanAuthorityUpdate, db: Session = Depends(get_domain_db)
) -> HumanAuthorityRead:
    try:
        repo = DomainRepository(db)
        authority = repo.get(HumanAuthority, authority_id)
        if authority is None:
            raise HTTPException(status_code=404, detail="AUTHORITY_NOT_FOUND")
        service = DomainService(db)
        updated = service.update_human_authority(
            authority=authority,
            display_name=payload.display_name,
            role_title=payload.role_title,
            active=payload.active,
            can_submit_human_decision=payload.can_submit_human_decision,
            can_approve_learning=payload.can_approve_learning,
            can_authorize_recall=payload.can_authorize_recall,
            actor="api-user",
        )
        service.commit()
        return _human_authority_read(updated)
    except HTTPException:
        db.rollback()
        raise
    except SQLAlchemyError as exc:
        db.rollback()
        raise HTTPException(status_code=503, detail=f"DATABASE_UNAVAILABLE: {exc.__class__.__name__}") from exc


@router.get("/ownership", response_model=list[ResponsibilityAssignmentRead])
def list_responsibility_assignments(db: Session = Depends(get_domain_db)) -> list[ResponsibilityAssignmentRead]:
    try:
        items = DomainRepository(db).list_responsibility_assignments()
        return [_responsibility_read(item, db) for item in items]
    except HTTPException:
        raise
    except SQLAlchemyError as exc:
        raise HTTPException(status_code=503, detail=f"DATABASE_UNAVAILABLE: {exc.__class__.__name__}") from exc


@router.post("/ownership", response_model=ResponsibilityAssignmentRead, status_code=201)
def create_responsibility_assignment(
    payload: ResponsibilityAssignmentCreate, db: Session = Depends(get_domain_db)
) -> ResponsibilityAssignmentRead:
    try:
        if payload.responsibility_type not in RESPONSIBILITY_ALLOWED[payload.scope_type]:
            raise HTTPException(status_code=422, detail="RESPONSIBILITY_ROLE_NOT_ALLOWED_FOR_SCOPE")
        _get_responsibility_scope(db, payload.scope_type, payload.scope_id)
        authority = db.get(HumanAuthority, payload.authority_id)
        if authority is None:
            raise HTTPException(status_code=404, detail="AUTHORITY_NOT_FOUND")
        if not authority.active:
            raise HTTPException(status_code=422, detail="AUTHORITY_INACTIVE")
        service = DomainService(db)
        try:
            assignment = service.assign_responsibility(
                scope_type=payload.scope_type,
                scope_id=payload.scope_id,
                responsibility_type=payload.responsibility_type,
                authority=authority,
                team_name=payload.team_name,
                actor="api-user",
            )
        except ValueError as exc:
            if str(exc) == "RESPONSIBILITY_ALREADY_ASSIGNED":
                raise HTTPException(status_code=409, detail=str(exc)) from exc
            raise HTTPException(status_code=422, detail=str(exc)) from exc
        service.commit()
        return _responsibility_read(assignment, db)
    except HTTPException:
        db.rollback()
        raise
    except SQLAlchemyError as exc:
        db.rollback()
        raise HTTPException(status_code=503, detail=f"DATABASE_UNAVAILABLE: {exc.__class__.__name__}") from exc


@router.patch("/ownership/{assignment_id}", response_model=ResponsibilityAssignmentRead)
def reassign_responsibility(
    assignment_id: str, payload: ResponsibilityAssignmentUpdate, db: Session = Depends(get_domain_db)
) -> ResponsibilityAssignmentRead:
    try:
        assignment = db.get(ResponsibilityAssignment, assignment_id)
        if assignment is None:
            raise HTTPException(status_code=404, detail="RESPONSIBILITY_NOT_FOUND")
        authority = db.get(HumanAuthority, payload.authority_id)
        if authority is None:
            raise HTTPException(status_code=404, detail="AUTHORITY_NOT_FOUND")
        if not authority.active:
            raise HTTPException(status_code=422, detail="AUTHORITY_INACTIVE")
        service = DomainService(db)
        updated = service.reassign_responsibility(
            assignment=assignment,
            authority=authority,
            team_name=payload.team_name,
            reason=payload.reason,
            actor="api-user",
        )
        service.commit()
        return _responsibility_read(updated, db)
    except HTTPException:
        db.rollback()
        raise
    except SQLAlchemyError as exc:
        db.rollback()
        raise HTTPException(status_code=503, detail=f"DATABASE_UNAVAILABLE: {exc.__class__.__name__}") from exc


@router.delete("/ownership/{assignment_id}", status_code=204)
def remove_responsibility(
    assignment_id: str, payload: ResponsibilityAssignmentRemove, db: Session = Depends(get_domain_db)
) -> None:
    try:
        assignment = db.get(ResponsibilityAssignment, assignment_id)
        if assignment is None:
            raise HTTPException(status_code=404, detail="RESPONSIBILITY_NOT_FOUND")
        service = DomainService(db)
        service.remove_responsibility(assignment=assignment, reason=payload.reason, actor="api-user")
        service.commit()
        return None
    except HTTPException:
        db.rollback()
        raise
    except SQLAlchemyError as exc:
        db.rollback()
        raise HTTPException(status_code=503, detail=f"DATABASE_UNAVAILABLE: {exc.__class__.__name__}") from exc


@router.get("/products", response_model=list[ProductRead])
def list_products(db: Session = Depends(get_domain_db)) -> list[ProductRead]:
    try:
        products = DomainRepository(db).list_products()
        return [ProductRead(id=item.id, name=item.name, description=item.description, active=item.active) for item in products]
    except SQLAlchemyError as exc:
        raise HTTPException(status_code=503, detail=f"DATABASE_UNAVAILABLE: {exc.__class__.__name__}") from exc


@router.post("/products", response_model=ProductRead, status_code=201)
def create_product(payload: ProductCreate, db: Session = Depends(get_domain_db)) -> ProductRead:
    try:
        service = DomainService(db)
        try:
            product = service.create_product(
                name=payload.name,
                description=payload.description,
                active=payload.active,
                actor="api-user",
            )
        except ValueError as exc:
            if str(exc) == "PRODUCT_NAME_ALREADY_EXISTS":
                raise HTTPException(status_code=409, detail=str(exc)) from exc
            raise
        service.commit()
        return ProductRead(id=product.id, name=product.name, description=product.description, active=product.active)
    except HTTPException:
        db.rollback()
        raise
    except SQLAlchemyError as exc:
        db.rollback()
        raise HTTPException(status_code=503, detail=f"DATABASE_UNAVAILABLE: {exc.__class__.__name__}") from exc


@router.patch("/products/{product_id}", response_model=ProductRead)
def update_product(product_id: str, payload: ProductUpdate, db: Session = Depends(get_domain_db)) -> ProductRead:
    try:
        product = db.get(Product, product_id)
        if product is None:
            raise HTTPException(status_code=404, detail="PRODUCT_NOT_FOUND")
        service = DomainService(db)
        updated = service.update_product(
            product=product,
            description=payload.description,
            active=payload.active,
            actor="api-user",
        )
        service.commit()
        return ProductRead(id=updated.id, name=updated.name, description=updated.description, active=updated.active)
    except HTTPException:
        db.rollback()
        raise
    except SQLAlchemyError as exc:
        db.rollback()
        raise HTTPException(status_code=503, detail=f"DATABASE_UNAVAILABLE: {exc.__class__.__name__}") from exc


@router.get("/modules", response_model=list[ModuleRead])
def list_modules(product_id: str | None = None, db: Session = Depends(get_domain_db)) -> list[ModuleRead]:
    try:
        modules = DomainRepository(db).list_modules(product_id=product_id)
        return [ModuleRead(id=item.id, product_id=item.product_id, name=item.name, description=item.description, active=item.active) for item in modules]
    except SQLAlchemyError as exc:
        raise HTTPException(status_code=503, detail=f"DATABASE_UNAVAILABLE: {exc.__class__.__name__}") from exc


@router.post("/modules", response_model=ModuleRead, status_code=201)
def create_module(payload: ModuleCreate, db: Session = Depends(get_domain_db)) -> ModuleRead:
    try:
        product = db.get(Product, payload.product_id)
        if product is None:
            raise HTTPException(status_code=404, detail="PRODUCT_NOT_FOUND")
        if not product.active:
            raise HTTPException(status_code=422, detail="PRODUCT_INACTIVE")
        service = DomainService(db)
        try:
            module = service.create_module(
                product=product,
                name=payload.name,
                description=payload.description,
                active=payload.active,
                actor="api-user",
            )
        except ValueError as exc:
            if str(exc) == "MODULE_NAME_ALREADY_EXISTS":
                raise HTTPException(status_code=409, detail=str(exc)) from exc
            raise
        service.commit()
        return ModuleRead(id=module.id, product_id=module.product_id, name=module.name, description=module.description, active=module.active)
    except HTTPException:
        db.rollback()
        raise
    except SQLAlchemyError as exc:
        db.rollback()
        raise HTTPException(status_code=503, detail=f"DATABASE_UNAVAILABLE: {exc.__class__.__name__}") from exc


@router.patch("/modules/{module_id}", response_model=ModuleRead)
def update_module(module_id: str, payload: ModuleUpdate, db: Session = Depends(get_domain_db)) -> ModuleRead:
    try:
        module = db.get(Module, module_id)
        if module is None:
            raise HTTPException(status_code=404, detail="MODULE_NOT_FOUND")
        service = DomainService(db)
        updated = service.update_module(
            module=module,
            description=payload.description,
            active=payload.active,
            actor="api-user",
        )
        service.commit()
        return ModuleRead(id=updated.id, product_id=updated.product_id, name=updated.name, description=updated.description, active=updated.active)
    except HTTPException:
        db.rollback()
        raise
    except SQLAlchemyError as exc:
        db.rollback()
        raise HTTPException(status_code=503, detail=f"DATABASE_UNAVAILABLE: {exc.__class__.__name__}") from exc


@router.get("/methods", response_model=list[DeliveryMethodRead])
def list_delivery_methods(db: Session = Depends(get_domain_db)) -> list[DeliveryMethodRead]:
    try:
        return [_delivery_method_read(item) for item in DomainRepository(db).list_delivery_methods()]
    except SQLAlchemyError as exc:
        raise HTTPException(status_code=503, detail=f"DATABASE_UNAVAILABLE: {exc.__class__.__name__}") from exc


@router.post("/methods", response_model=DeliveryMethodRead, status_code=201)
def create_delivery_method(payload: DeliveryMethodCreate, db: Session = Depends(get_domain_db)) -> DeliveryMethodRead:
    try:
        repo = DomainRepository(db)
        module = repo.get(Module, payload.module_id)
        if module is None:
            raise HTTPException(status_code=404, detail="MODULE_NOT_FOUND")
        service = DomainService(db)
        method = service.create_delivery_method(
            module=module,
            name=payload.name,
            description=payload.description,
            actor="api-user",
        )
        service.commit()
        return _delivery_method_read(method)
    except HTTPException:
        db.rollback()
        raise
    except SQLAlchemyError as exc:
        db.rollback()
        raise HTTPException(status_code=503, detail=f"DATABASE_UNAVAILABLE: {exc.__class__.__name__}") from exc


@router.get("/method-versions", response_model=list[MethodVersionRead])
def list_method_versions(db: Session = Depends(get_domain_db)) -> list[MethodVersionRead]:
    try:
        return [_method_version_read(item, db) for item in DomainRepository(db).list_method_versions()]
    except SQLAlchemyError as exc:
        raise HTTPException(status_code=503, detail=f"DATABASE_UNAVAILABLE: {exc.__class__.__name__}") from exc


@router.post("/method-versions", response_model=MethodVersionRead, status_code=201)
def create_method_version(payload: MethodVersionCreate, db: Session = Depends(get_domain_db)) -> MethodVersionRead:
    try:
        repo = DomainRepository(db)
        method = repo.get(DeliveryMethod, payload.method_id)
        if method is None:
            raise HTTPException(status_code=404, detail="METHOD_NOT_FOUND")
        service = DomainService(db)
        version = service.create_method_version(
            method=method,
            version=payload.version,
            summary=payload.summary,
            actor="api-user",
        )
        service.commit()
        return _method_version_read(version, db)
    except HTTPException:
        db.rollback()
        raise
    except SQLAlchemyError as exc:
        db.rollback()
        raise HTTPException(status_code=503, detail=f"DATABASE_UNAVAILABLE: {exc.__class__.__name__}") from exc


@router.post("/method-versions/{version_id}/baseline-approval", response_model=MethodVersionRead)
def approve_baseline_method_version(
    version_id: str,
    payload: MethodVersionBaselineApproval,
    x_creed_principal: str | None = Header(default=None, alias="X-CREED-Principal"),
    db: Session = Depends(get_domain_db),
) -> MethodVersionRead:
    try:
        repo = DomainRepository(db)
        version = repo.get(MethodVersion, version_id)
        if version is None:
            raise HTTPException(status_code=404, detail="METHOD_VERSION_NOT_FOUND")
        try:
            authority = require_human_authority(
                db,
                principal=x_creed_principal,
                capability="can_approve_learning",
                claimed_reviewer=payload.reviewer,
            )
        except AuthorityEnforcementError as exc:
            raise HTTPException(status_code=403, detail=str(exc)) from exc

        service = DomainService(db)
        try:
            approved = service.approve_baseline_method_version(
                method_version=version,
                authority=authority,
                reason=payload.reason,
            )
        except ValueError as exc:
            if str(exc) in {"METHOD_VERSION_NOT_DRAFT", "METHOD_BASELINE_ALREADY_ESTABLISHED"}:
                raise HTTPException(status_code=409, detail=str(exc)) from exc
            raise
        service.commit()
        return _method_version_read(approved, db)
    except HTTPException:
        db.rollback()
        raise
    except SQLAlchemyError as exc:
        db.rollback()
        raise HTTPException(status_code=503, detail=f"DATABASE_UNAVAILABLE: {exc.__class__.__name__}") from exc


@router.get("/implementations", response_model=list[ImplementationRead])
def list_implementations(db: Session = Depends(get_domain_db)) -> list[ImplementationRead]:
    try:
        return [_implementation_read(item) for item in DomainRepository(db).list_implementations()]
    except SQLAlchemyError as exc:
        raise HTTPException(status_code=503, detail=f"DATABASE_UNAVAILABLE: {exc.__class__.__name__}") from exc


@router.post("/implementations", response_model=ImplementationRead, status_code=201)
def create_implementation(payload: ImplementationCreate, db: Session = Depends(get_domain_db)) -> ImplementationRead:
    try:
        repo = DomainRepository(db)
        client = repo.get(Client, payload.client_id)
        if client is None:
            raise HTTPException(status_code=404, detail="CLIENT_NOT_FOUND")
        product = repo.get(Product, payload.product_id)
        if product is None:
            raise HTTPException(status_code=404, detail="PRODUCT_NOT_FOUND")
        module = repo.get(Module, payload.module_id)
        if module is None:
            raise HTTPException(status_code=404, detail="MODULE_NOT_FOUND")
        if module.product_id != product.id:
            raise HTTPException(status_code=422, detail="MODULE_PRODUCT_MISMATCH")

        service = DomainService(db)
        implementation = service.create_implementation(
            client=client,
            product=product,
            module=module,
            name=payload.name,
            release_version=payload.release_version,
            actor="api-user",
        )
        service.commit()
        return _implementation_read(implementation)
    except HTTPException:
        db.rollback()
        raise
    except SQLAlchemyError as exc:
        db.rollback()
        raise HTTPException(status_code=503, detail=f"DATABASE_UNAVAILABLE: {exc.__class__.__name__}") from exc


@router.get("/deployments", response_model=list[DeploymentRead])
def list_deployments(db: Session = Depends(get_domain_db)) -> list[DeploymentRead]:
    try:
        return [_deployment_read(item) for item in DomainRepository(db).list_deployments()]
    except SQLAlchemyError as exc:
        raise HTTPException(status_code=503, detail=f"DATABASE_UNAVAILABLE: {exc.__class__.__name__}") from exc


@router.post("/deployments", response_model=DeploymentRead, status_code=201)
def record_deployment(payload: DeploymentCreate, db: Session = Depends(get_domain_db)) -> DeploymentRead:
    try:
        repo = DomainRepository(db)
        implementation = repo.get(Implementation, payload.implementation_id)
        if implementation is None:
            raise HTTPException(status_code=404, detail="IMPLEMENTATION_NOT_FOUND")
        evidence = repo.get(EvidenceDocument, payload.evidence_document_id)
        if evidence is None:
            raise HTTPException(status_code=404, detail="EVIDENCE_DOCUMENT_NOT_FOUND")

        deployed_at = payload.deployed_at
        if deployed_at.tzinfo is None:
            deployed_at = deployed_at.replace(tzinfo=timezone.utc)
        else:
            deployed_at = deployed_at.astimezone(timezone.utc)

        service = DomainService(db)
        try:
            deployment = service.record_deployment(
                implementation=implementation,
                environment=payload.environment,
                deployed_at=deployed_at,
                evidence_document=evidence,
                deployment_reference=payload.deployment_reference,
                notes=payload.notes,
                actor="api-user",
            )
        except ValueError as exc:
            if str(exc) == "DEPLOYMENT_EVENT_ALREADY_EXISTS":
                raise HTTPException(status_code=409, detail=str(exc)) from exc
            raise HTTPException(status_code=422, detail=str(exc)) from exc
        service.commit()
        return _deployment_read(deployment)
    except HTTPException:
        db.rollback()
        raise
    except SQLAlchemyError as exc:
        db.rollback()
        raise HTTPException(status_code=503, detail=f"DATABASE_UNAVAILABLE: {exc.__class__.__name__}") from exc


@router.get("/dependencies", response_model=list[ImplementationMethodDependencyRead])
def list_implementation_method_dependencies(
    db: Session = Depends(get_domain_db),
) -> list[ImplementationMethodDependencyRead]:
    try:
        items = DomainRepository(db).list_implementation_method_dependencies()
        return [_implementation_method_dependency_read(item, db) for item in items]
    except HTTPException:
        raise
    except SQLAlchemyError as exc:
        raise HTTPException(status_code=503, detail=f"DATABASE_UNAVAILABLE: {exc.__class__.__name__}") from exc


@router.post("/dependencies", response_model=ImplementationMethodDependencyRead, status_code=201)
def register_implementation_method_dependency(
    payload: ImplementationMethodDependencyCreate,
    db: Session = Depends(get_domain_db),
) -> ImplementationMethodDependencyRead:
    try:
        repo = DomainRepository(db)
        implementation = repo.get(Implementation, payload.implementation_id)
        if implementation is None:
            raise HTTPException(status_code=404, detail="IMPLEMENTATION_NOT_FOUND")
        method_version = repo.get(MethodVersion, payload.method_version_id)
        if method_version is None:
            raise HTTPException(status_code=404, detail="METHOD_VERSION_NOT_FOUND")
        evidence = repo.get(EvidenceDocument, payload.evidence_document_id)
        if evidence is None:
            raise HTTPException(status_code=404, detail="EVIDENCE_DOCUMENT_NOT_FOUND")
        if method_version.method.module_id != implementation.module_id:
            raise HTTPException(status_code=422, detail="IMPLEMENTATION_METHOD_MODULE_MISMATCH")

        service = DomainService(db)
        try:
            edge = service.register_implementation_method_dependency(
                implementation=implementation,
                method_version=method_version,
                evidence_document=evidence,
                actor="api-user",
            )
        except ValueError as exc:
            if str(exc) == "DEPENDENCY_ALREADY_EXISTS_WITH_DIFFERENT_EVIDENCE":
                raise HTTPException(status_code=409, detail=str(exc)) from exc
            raise HTTPException(status_code=422, detail=str(exc)) from exc
        service.commit()
        return _implementation_method_dependency_read(edge, db)
    except HTTPException:
        db.rollback()
        raise
    except SQLAlchemyError as exc:
        db.rollback()
        raise HTTPException(status_code=503, detail=f"DATABASE_UNAVAILABLE: {exc.__class__.__name__}") from exc


@router.delete("/dependencies/{dependency_id}", status_code=204)
def remove_implementation_method_dependency(
    dependency_id: str,
    payload: ImplementationMethodDependencyRemove,
    db: Session = Depends(get_domain_db),
) -> None:
    try:
        repo = DomainRepository(db)
        edge = repo.get(DependencyEdge, dependency_id)
        if edge is None:
            raise HTTPException(status_code=404, detail="DEPENDENCY_NOT_FOUND")
        if not (
            edge.source_type == "Implementation"
            and edge.target_type == "MethodVersion"
            and edge.relationship == "USES_METHOD_VERSION"
        ):
            raise HTTPException(status_code=422, detail="NOT_IMPLEMENTATION_METHOD_DEPENDENCY")
        service = DomainService(db)
        service.remove_implementation_method_dependency(
            edge=edge,
            reason=payload.reason,
            actor="api-user",
        )
        service.commit()
        return None
    except HTTPException:
        db.rollback()
        raise
    except SQLAlchemyError as exc:
        db.rollback()
        raise HTTPException(status_code=503, detail=f"DATABASE_UNAVAILABLE: {exc.__class__.__name__}") from exc
