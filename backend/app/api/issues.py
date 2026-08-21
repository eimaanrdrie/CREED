from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Response
from pydantic import BaseModel, Field, field_validator
from sqlalchemy import func, select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session, selectinload

from app.api.domain import get_domain_db
from app.domain.enums import IssueSeverity, IssueStatus, IssueType
from app.domain.models import AuditEvent, Client, IssueEvidenceLink, SupportIssue, uuid_str

router = APIRouter(prefix="/issues", tags=["issues"])


class IssueCreate(BaseModel):
    external_ticket_id: str | None = Field(default=None, max_length=120)
    client_id: str | None = None
    title: str = Field(min_length=4, max_length=300)
    description: str = Field(min_length=8, max_length=20000)
    issue_type: IssueType = IssueType.UNKNOWN
    severity: IssueSeverity = IssueSeverity.UNKNOWN

    @field_validator("external_ticket_id", "client_id")
    @classmethod
    def empty_to_none(cls, value: str | None) -> str | None:
        if value is None:
            return None
        cleaned = value.strip()
        return cleaned or None

    @field_validator("title", "description")
    @classmethod
    def strip_required(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("must not be blank")
        return cleaned


class IssueAttachmentRead(BaseModel):
    id: str
    document_id: str
    title: str
    original_filename: str | None
    document_type: str
    parse_status: str
    index_status: str
    created_at: datetime


class IssueRead(BaseModel):
    id: str
    external_ticket_id: str | None
    client_id: str | None
    client_name: str | None
    title: str
    description: str
    issue_type: str
    severity: str
    status: str
    attachment_count: int
    created_at: datetime
    updated_at: datetime


class IssueDetail(IssueRead):
    attachments: list[IssueAttachmentRead]
    metadata: dict


def _issue_read(issue: SupportIssue, attachment_count: int | None = None) -> IssueRead:
    if attachment_count is None:
        attachment_count = len(issue.evidence_links)
    return IssueRead(
        id=issue.id,
        external_ticket_id=issue.external_ticket_id,
        client_id=issue.client_id,
        client_name=issue.client.name if issue.client else None,
        title=issue.title,
        description=issue.description,
        issue_type=issue.issue_type,
        severity=issue.severity,
        status=issue.status,
        attachment_count=attachment_count,
        created_at=issue.created_at,
        updated_at=issue.updated_at,
    )


def _issue_detail(issue: SupportIssue) -> IssueDetail:
    base = _issue_read(issue).model_dump()
    attachments = [
        IssueAttachmentRead(
            id=link.id,
            document_id=link.document.id,
            title=link.document.title,
            original_filename=link.document.original_filename,
            document_type=link.document.document_type,
            parse_status=link.document.parse_status,
            index_status=link.document.index_status,
            created_at=link.created_at,
        )
        for link in sorted(issue.evidence_links, key=lambda item: item.created_at)
    ]
    return IssueDetail(**base, attachments=attachments, metadata=issue.metadata_json if hasattr(issue, "metadata_json") else {})


@router.get("", response_model=list[IssueRead])
def list_issues(db: Session = Depends(get_domain_db)) -> list[IssueRead]:
    try:
        count_subq = (
            select(IssueEvidenceLink.issue_id, func.count(IssueEvidenceLink.id).label("attachment_count"))
            .group_by(IssueEvidenceLink.issue_id)
            .subquery()
        )
        rows = db.execute(
            select(SupportIssue, func.coalesce(count_subq.c.attachment_count, 0))
            .outerjoin(count_subq, count_subq.c.issue_id == SupportIssue.id)
            .options(selectinload(SupportIssue.client))
            .order_by(SupportIssue.created_at.desc())
        ).all()
        return [_issue_read(issue, int(count)) for issue, count in rows]
    except SQLAlchemyError as exc:
        raise HTTPException(status_code=503, detail=f"DATABASE_UNAVAILABLE: {exc.__class__.__name__}") from exc


@router.get("/{issue_id}", response_model=IssueDetail)
def get_issue(issue_id: str, db: Session = Depends(get_domain_db)) -> IssueDetail:
    issue = db.scalar(
        select(SupportIssue)
        .where(SupportIssue.id == issue_id)
        .options(
            selectinload(SupportIssue.client),
            selectinload(SupportIssue.evidence_links).selectinload(IssueEvidenceLink.document),
        )
    )
    if issue is None:
        raise HTTPException(status_code=404, detail="ISSUE_NOT_FOUND")
    return _issue_detail(issue)


@router.post("", response_model=IssueDetail, status_code=201)
def create_issue(payload: IssueCreate, response: Response, db: Session = Depends(get_domain_db)) -> IssueDetail:
    if payload.client_id is not None and db.get(Client, payload.client_id) is None:
        raise HTTPException(status_code=422, detail="CLIENT_NOT_FOUND")

    # M19: support-ticket submission is idempotent for the same client/ticket/content.
    if payload.external_ticket_id:
        existing = db.scalar(
            select(SupportIssue).where(
                SupportIssue.external_ticket_id == payload.external_ticket_id,
                SupportIssue.client_id == payload.client_id,
            ).order_by(SupportIssue.created_at.desc()).limit(1)
        )
        if existing is not None:
            same = existing.title.strip() == payload.title.strip() and existing.description.strip() == payload.description.strip()
            if not same:
                raise HTTPException(status_code=409, detail="SUPPORT_TICKET_CONFLICT")
            response.status_code = 200
            loaded = db.scalar(
                select(SupportIssue).where(SupportIssue.id == existing.id).options(
                    selectinload(SupportIssue.client),
                    selectinload(SupportIssue.evidence_links).selectinload(IssueEvidenceLink.document),
                )
            )
            assert loaded is not None
            return _issue_detail(loaded)

    issue = SupportIssue(
        id=uuid_str(),
        external_ticket_id=payload.external_ticket_id,
        client_id=payload.client_id,
        title=payload.title,
        description=payload.description,
        issue_type=payload.issue_type.value,
        severity=payload.severity.value,
        status=IssueStatus.OPEN.value,
    )
    audit = AuditEvent(
        actor="demo-operator",
        action="ISSUE_CREATED",
        object_type="SupportIssue",
        object_id=issue.id,
        metadata_json={
            "ticket_id": payload.external_ticket_id,
            "issue_type": payload.issue_type.value,
            "severity": payload.severity.value,
            "client_id": payload.client_id,
        },
    )
    try:
        db.add_all([issue, audit])
        db.commit()
    except SQLAlchemyError as exc:
        db.rollback()
        raise HTTPException(status_code=503, detail=f"DATABASE_UNAVAILABLE: {exc.__class__.__name__}") from exc

    created = db.scalar(
        select(SupportIssue)
        .where(SupportIssue.id == issue.id)
        .options(
            selectinload(SupportIssue.client),
            selectinload(SupportIssue.evidence_links).selectinload(IssueEvidenceLink.document),
        )
    )
    assert created is not None
    return _issue_detail(created)
