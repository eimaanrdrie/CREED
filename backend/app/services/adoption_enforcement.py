from __future__ import annotations

import hashlib
import json
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.domain.models import (
    AdoptionReceipt,
    AdoptionReceiptDetail,
    DeliveryMethod,
    Implementation,
    LearningProposal,
    MethodVersion,
)

SUPPORTED_SCOPE_MODES = {
    "METHOD_CATALOG",
    "CURRENT_REGISTERED_IMPLEMENTATIONS",
    "SELECTED_IMPLEMENTATIONS",
}


def _canonical_hash(payload: dict[str, Any]) -> str:
    raw = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        default=str,
    ).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def _learning_for_version(db: Session, method_version_id: str) -> LearningProposal | None:
    return db.scalar(
        select(LearningProposal)
        .where(LearningProposal.proposed_method_version_id == method_version_id)
        .order_by(LearningProposal.created_at.desc())
        .limit(1)
    )


def adoption_policy_for_version(db: Session, method_version_id: str) -> dict[str, Any] | None:
    """Return the persisted adoption policy for a learned Method Version.

    Baseline/manual versions intentionally return ``None`` so pre-learning catalog behavior
    remains unchanged. Learned versions fail closed unless their approval receipt exists,
    verifies, and contains an R94-M08 structured scope.
    """
    version = db.get(MethodVersion, method_version_id)
    if version is None:
        raise ValueError("METHOD_VERSION_NOT_FOUND")

    learning = _learning_for_version(db, version.id)
    if learning is None:
        return None

    result: dict[str, Any] = {
        "enforced": True,
        "learning_id": learning.id,
        "learning_status": learning.status,
        "receipt_id": None,
        "receipt_integrity": None,
        "scope_mode": None,
        "implementation_ids": [],
        "reason": "READY",
    }

    if learning.status != "APPROVED" or version.status != "APPROVED":
        result["reason"] = "LEARNED_METHOD_VERSION_NOT_APPROVED_FOR_ADOPTION"
        return result

    receipt = db.scalar(select(AdoptionReceipt).where(AdoptionReceipt.learning_id == learning.id).limit(1))
    if receipt is None:
        result["reason"] = "ADOPTION_RECEIPT_REQUIRED_FOR_LEARNED_VERSION"
        return result

    result["receipt_id"] = receipt.id
    detail = db.scalar(
        select(AdoptionReceiptDetail)
        .where(AdoptionReceiptDetail.receipt_id == receipt.id)
        .limit(1)
    )
    if detail is None:
        result["reason"] = "ADOPTION_RECEIPT_DETAIL_REQUIRED"
        return result

    valid = _canonical_hash(detail.receipt_payload_json or {}) == receipt.content_hash
    result["receipt_integrity"] = "VALID" if valid else "INVALID"
    if not valid:
        result["reason"] = "ADOPTION_RECEIPT_INTEGRITY_INVALID"
        return result

    scope = receipt.adoption_scope or {}
    mode = str(scope.get("mode") or "").strip().upper()
    implementation_ids = scope.get("implementation_ids") or []
    if (
        mode not in SUPPORTED_SCOPE_MODES
        or not isinstance(implementation_ids, list)
        or any(not isinstance(item, str) for item in implementation_ids)
    ):
        result["reason"] = "ADOPTION_SCOPE_REQUIRED_FOR_LEARNED_VERSION"
        return result

    adopted = scope.get("adopted_method_version") or {}
    if adopted.get("id") != version.id:
        result["reason"] = "ADOPTION_SCOPE_METHOD_VERSION_MISMATCH"
        return result

    result["scope_mode"] = mode
    result["implementation_ids"] = sorted(set(item for item in implementation_ids if item))
    return result


def adoption_eligibility(
    db: Session,
    *,
    method_version: MethodVersion,
    implementation: Implementation,
) -> dict[str, Any]:
    """Evaluate whether one implementation may explicitly adopt a Method Version.

    No learning proposal means the historical baseline/catalog behavior is untouched.
    When a Method Version originates from governed learning, its signed Adoption Receipt
    is the authoritative reuse boundary.
    """
    policy = adoption_policy_for_version(db, method_version.id)
    if policy is None:
        return {
            "enforced": False,
            "allowed": True,
            "reason": "BASELINE_OR_LEGACY_VERSION",
            "scope_mode": None,
            "receipt_id": None,
            "receipt_integrity": None,
            "implementation_ids": [],
        }

    response = {**policy, "allowed": False}
    if policy["reason"] != "READY":
        return response

    method = db.get(DeliveryMethod, method_version.method_id)
    if method is None or implementation.module_id != method.module_id:
        response["reason"] = "IMPLEMENTATION_METHOD_MODULE_MISMATCH"
        return response

    mode = policy["scope_mode"]
    if mode == "METHOD_CATALOG":
        response["allowed"] = True
        response["reason"] = "METHOD_CATALOG_SCOPE"
        return response

    if implementation.id in set(policy["implementation_ids"]):
        response["allowed"] = True
        response["reason"] = "IMPLEMENTATION_WITHIN_SIGNED_SCOPE"
        return response

    response["reason"] = "ADOPTION_SCOPE_EXCLUDES_IMPLEMENTATION"
    return response
