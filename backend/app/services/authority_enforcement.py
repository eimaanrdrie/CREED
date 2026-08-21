from __future__ import annotations

from typing import Literal

from sqlalchemy.orm import Session

from app.domain.models import HumanAuthority
from app.repositories.domain import DomainRepository

AuthorityCapability = Literal[
    "can_submit_human_decision",
    "can_approve_learning",
    "can_authorize_recall",
]


class AuthorityEnforcementError(ValueError):
    """Raised when a governed action does not satisfy the configured authority registry."""


_PERMISSION_CODES: dict[AuthorityCapability, str] = {
    "can_submit_human_decision": "HUMAN_DECISION_AUTHORITY_REQUIRED",
    "can_approve_learning": "LEARNING_APPROVAL_AUTHORITY_REQUIRED",
    "can_authorize_recall": "RECALL_AUTHORITY_REQUIRED",
}


def require_human_authority(
    db: Session,
    *,
    principal: str | None,
    capability: AuthorityCapability,
    claimed_reviewer: str | None = None,
) -> HumanAuthority:
    cleaned = (principal or "").strip()
    if not cleaned:
        raise AuthorityEnforcementError("AUTHORITY_PRINCIPAL_REQUIRED")

    authority = DomainRepository(db).get_human_authority_by_principal(cleaned)
    if authority is None:
        raise AuthorityEnforcementError("AUTHORITY_PRINCIPAL_NOT_REGISTERED")
    if not authority.active:
        raise AuthorityEnforcementError("AUTHORITY_PRINCIPAL_INACTIVE")
    if not bool(getattr(authority, capability)):
        raise AuthorityEnforcementError(_PERMISSION_CODES[capability])

    if claimed_reviewer is not None and claimed_reviewer.strip() != authority.principal:
        raise AuthorityEnforcementError("AUTHORITY_PRINCIPAL_MISMATCH")

    return authority
