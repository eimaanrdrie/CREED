from __future__ import annotations

import json
from datetime import datetime

import httpx
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field, field_validator
from pydantic_core import ValidationError
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session, selectinload

from app.api.domain import get_domain_db
from app.domain.models import IssueUnderstanding, SupportIssue
from app.services.issue_understanding import (
    IssueTypeLiteral,
    SeverityLiteral,
    run_issue_understanding,
    verify_issue_understanding,
)

router = APIRouter(prefix="/issues", tags=["issue-understanding"])


class UnderstandingRead(BaseModel):
    id: str
    issue_id: str
    qwen_run_id: str
    input_hash: str
    configured_model: str
    actual_model: str | None
    duration_ms: float | None
    prompt_eval_count: int | None
    eval_count: int | None
    client_name: str | None
    product: str | None
    module: str | None
    issue_type: str
    summary: str
    suspected_function: str | None
    keywords: list[str]
    severity: str
    confidence: float
    status: str
    human_verified_by: str | None
    human_verified_at: datetime | None
    created_at: datetime
    updated_at: datetime
    warnings: list[str]


class UnderstandingEdit(BaseModel):
    client_name: str | None = Field(default=None, max_length=180)
    product: str | None = Field(default=None, max_length=180)
    module: str | None = Field(default=None, max_length=180)
    issue_type: IssueTypeLiteral
    summary: str = Field(min_length=8, max_length=800)
    suspected_function: str | None = Field(default=None, max_length=300)
    keywords: list[str] = Field(default_factory=list, max_length=8)
    severity: SeverityLiteral

    @field_validator("summary")
    @classmethod
    def summary_not_blank(cls, value: str) -> str:
        cleaned = " ".join(value.split())
        if len(cleaned) < 8:
            raise ValueError("summary must contain at least 8 characters")
        return cleaned


def _warnings(issue: SupportIssue, understanding: IssueUnderstanding) -> list[str]:
    warnings: list[str] = []
    if issue.client and understanding.client_name and issue.client.name.casefold() != understanding.client_name.casefold():
        warnings.append("AI_CLIENT_DIFFERS_FROM_HUMAN_SELECTED_CLIENT")
    if issue.issue_type != "UNKNOWN" and issue.issue_type != understanding.issue_type:
        warnings.append("AI_TYPE_DIFFERS_FROM_HUMAN_REPORTED_TYPE")
    if issue.severity != "UNKNOWN" and issue.severity != understanding.severity:
        warnings.append("AI_SEVERITY_DIFFERS_FROM_HUMAN_REPORTED_SEVERITY")
    if understanding.product is None:
        warnings.append("PRODUCT_NOT_VERIFIED_FROM_ISSUE_TEXT")
    if understanding.module is None:
        warnings.append("MODULE_NOT_VERIFIED_FROM_ISSUE_TEXT")
    return warnings


def _read(issue: SupportIssue, understanding: IssueUnderstanding) -> UnderstandingRead:
    return UnderstandingRead(
        id=understanding.id,
        issue_id=understanding.issue_id,
        qwen_run_id=understanding.qwen_run_id,
        input_hash=understanding.input_hash,
        configured_model=understanding.configured_model,
        actual_model=understanding.actual_model,
        duration_ms=understanding.duration_ms,
        prompt_eval_count=understanding.prompt_eval_count,
        eval_count=understanding.eval_count,
        client_name=understanding.client_name,
        product=understanding.product,
        module=understanding.module,
        issue_type=understanding.issue_type,
        summary=understanding.summary,
        suspected_function=understanding.suspected_function,
        keywords=list(understanding.keywords_json or []),
        severity=understanding.severity,
        confidence=understanding.confidence,
        status=understanding.status,
        human_verified_by=understanding.human_verified_by,
        human_verified_at=understanding.human_verified_at,
        created_at=understanding.created_at,
        updated_at=understanding.updated_at,
        warnings=_warnings(issue, understanding),
    )


def _load_issue(db: Session, issue_id: str) -> SupportIssue:
    issue = db.scalar(select(SupportIssue).where(SupportIssue.id == issue_id).options(selectinload(SupportIssue.client)))
    if issue is None:
        raise HTTPException(status_code=404, detail="ISSUE_NOT_FOUND")
    return issue


@router.get("/{issue_id}/understanding", response_model=UnderstandingRead | None)
def get_latest_understanding(issue_id: str, db: Session = Depends(get_domain_db)) -> UnderstandingRead | None:
    issue = _load_issue(db, issue_id)
    understanding = db.scalar(
        select(IssueUnderstanding)
        .where(IssueUnderstanding.issue_id == issue_id)
        .order_by(IssueUnderstanding.created_at.desc())
        .limit(1)
    )
    return _read(issue, understanding) if understanding else None


@router.post("/{issue_id}/understand", response_model=UnderstandingRead, status_code=201)
def understand_issue(issue_id: str, db: Session = Depends(get_domain_db)) -> UnderstandingRead:
    issue = _load_issue(db, issue_id)
    try:
        understanding = run_issue_understanding(db, issue)
    except httpx.HTTPError as exc:
        db.rollback()
        raise HTTPException(status_code=503, detail=f"QWEN_RUNTIME_UNAVAILABLE: {exc.__class__.__name__}") from exc
    except (ValidationError, json.JSONDecodeError, ValueError) as exc:
        db.rollback()
        raise HTTPException(status_code=502, detail=f"AI_OUTPUT_VALIDATION_FAILED: {exc.__class__.__name__}") from exc
    except SQLAlchemyError as exc:
        db.rollback()
        raise HTTPException(status_code=503, detail=f"DATABASE_UNAVAILABLE: {exc.__class__.__name__}") from exc
    return _read(issue, understanding)


@router.patch("/{issue_id}/understanding/{understanding_id}", response_model=UnderstandingRead)
def edit_understanding(
    issue_id: str,
    understanding_id: str,
    payload: UnderstandingEdit,
    db: Session = Depends(get_domain_db),
) -> UnderstandingRead:
    issue = _load_issue(db, issue_id)
    understanding = db.scalar(
        select(IssueUnderstanding).where(
            IssueUnderstanding.id == understanding_id,
            IssueUnderstanding.issue_id == issue_id,
        )
    )
    if understanding is None:
        raise HTTPException(status_code=404, detail="ISSUE_UNDERSTANDING_NOT_FOUND")
    try:
        understanding = verify_issue_understanding(
            db,
            understanding,
            client_name=payload.client_name,
            product=payload.product,
            module=payload.module,
            issue_type=payload.issue_type,
            summary=payload.summary,
            suspected_function=payload.suspected_function,
            keywords=payload.keywords,
            severity=payload.severity,
        )
    except SQLAlchemyError as exc:
        db.rollback()
        raise HTTPException(status_code=503, detail=f"DATABASE_UNAVAILABLE: {exc.__class__.__name__}") from exc
    return _read(issue, understanding)
