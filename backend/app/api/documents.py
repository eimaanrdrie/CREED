from __future__ import annotations

from datetime import datetime
import hashlib
from pathlib import Path

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.api.domain import get_domain_db
from app.core.config import get_settings
from app.domain.models import AuditEvent, EvidenceDocument, IssueEvidenceLink, SupportIssue, uuid_str
from app.services.documents import DocumentIngestionError, parse_document, persist_file
from app.services.retrieval import RetrievalService

router = APIRouter(prefix="/documents", tags=["documents"])


class DocumentRead(BaseModel):
    id: str
    source: str
    title: str
    document_type: str
    version: str | None
    content_hash: str
    original_filename: str | None
    mime_type: str | None
    file_size: int | None
    parse_status: str
    char_count: int
    uploaded_at: datetime
    metadata: dict
    index_status: str
    chunk_count: int
    embedding_model: str | None
    embedding_degraded: bool


class DocumentDetail(DocumentRead):
    extracted_text: str


def to_read(item: EvidenceDocument) -> DocumentRead:
    return DocumentRead(
        id=item.id,
        source=item.source,
        title=item.title,
        document_type=item.document_type,
        version=item.version,
        content_hash=item.content_hash,
        original_filename=item.original_filename,
        mime_type=item.mime_type,
        file_size=item.file_size,
        parse_status=item.parse_status,
        char_count=item.char_count or 0,
        uploaded_at=item.uploaded_at,
        metadata=item.metadata_json,
        index_status=item.index_status,
        chunk_count=item.chunk_count or 0,
        embedding_model=item.embedding_model,
        embedding_degraded=bool(item.embedding_degraded),
    )


@router.get("", response_model=list[DocumentRead])
def list_documents(db: Session = Depends(get_domain_db)) -> list[DocumentRead]:
    try:
        items = list(db.scalars(select(EvidenceDocument).order_by(EvidenceDocument.uploaded_at.desc())))
        return [to_read(item) for item in items]
    except SQLAlchemyError as exc:
        raise HTTPException(status_code=503, detail=f"DATABASE_UNAVAILABLE: {exc.__class__.__name__}") from exc


@router.get("/{document_id}", response_model=DocumentDetail)
def get_document(document_id: str, db: Session = Depends(get_domain_db)) -> DocumentDetail:
    item = db.get(EvidenceDocument, document_id)
    if item is None:
        raise HTTPException(status_code=404, detail="DOCUMENT_NOT_FOUND")
    base = to_read(item).model_dump()
    return DocumentDetail(**base, extracted_text=item.extracted_text or "")


def _path_within(path: Path, root: Path) -> bool:
    try:
        path.relative_to(root)
        return True
    except ValueError:
        return False


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    try:
        with path.open("rb") as handle:
            for chunk in iter(lambda: handle.read(1024 * 1024), b""):
                digest.update(chunk)
    except OSError as exc:
        raise HTTPException(status_code=503, detail=f"ORIGINAL_FILE_UNAVAILABLE: {exc.__class__.__name__}") from exc
    return digest.hexdigest()


def _safe_original_name(item: EvidenceDocument) -> str | None:
    name = str(item.original_filename or "").strip()
    if not name:
        return None
    safe = Path(name).name
    return safe if safe == name else None


def _verified_original_path(item: EvidenceDocument) -> Path:
    settings = get_settings()
    upload_root = settings.document_storage_dir.expanduser().resolve()
    backend_root = Path(__file__).resolve().parents[2]
    demo_root = (backend_root / "demo_data").resolve()
    safe_name = _safe_original_name(item)

    # Build every legitimate location that can represent this document. Older
    # records may contain a relative path resolved against the Uvicorn launch
    # directory, while newer records are stored under the canonical governed
    # document root. We recover only inside governed roots and still require the
    # persisted SHA-256 to match before serving any bytes.
    candidates: list[Path] = []

    def add_candidate(path: Path, allowed_root: Path) -> None:
        resolved = path.expanduser().resolve()
        if _path_within(resolved, allowed_root) and resolved not in candidates:
            candidates.append(resolved)

    if item.storage_path:
        raw = Path(item.storage_path).expanduser()
        if raw.is_absolute():
            resolved = raw.resolve()
            if _path_within(resolved, upload_root):
                add_candidate(resolved, upload_root)
            if _path_within(resolved, demo_root):
                add_candidate(resolved, demo_root)
        else:
            # Legacy local runs could persist a relative path. Try both the new
            # stable backend anchor and the current process directory.
            add_candidate(backend_root / raw, upload_root)
            add_candidate(Path.cwd() / raw, upload_root)
            add_candidate(backend_root / raw, demo_root)
            add_candidate(Path.cwd() / raw, demo_root)

    # Canonical recovery path for uploaded documents. This makes old DB rows
    # resilient to backend restarts that use a different working directory.
    document_id = str(getattr(item, "id", "") or "").strip()
    if document_id and safe_name:
        add_candidate(upload_root / document_id / safe_name, upload_root)

    metadata = item.metadata_json or {}
    if metadata.get("synthetic") is True and safe_name:
        add_candidate(demo_root / safe_name, demo_root)

    if not candidates:
        if not item.storage_path and not (document_id and safe_name):
            raise HTTPException(status_code=404, detail="ORIGINAL_FILE_NOT_AVAILABLE")
        raise HTTPException(status_code=403, detail="ORIGINAL_FILE_PATH_NOT_ALLOWED")

    existing = [candidate for candidate in candidates if candidate.is_file()]
    if not existing:
        raise HTTPException(status_code=404, detail="ORIGINAL_FILE_NOT_FOUND")

    # Do not trust path identity alone. A recovered file is valid only when its
    # bytes exactly match the hash sealed at ingestion time. If one legacy path
    # is stale/tampered but the canonical copy is intact, prefer the valid copy.
    saw_hash_mismatch = False
    for candidate in existing:
        if _sha256_file(candidate) == item.content_hash:
            return candidate
        saw_hash_mismatch = True

    if saw_hash_mismatch:
        raise HTTPException(status_code=409, detail="ORIGINAL_FILE_HASH_MISMATCH")
    raise HTTPException(status_code=404, detail="ORIGINAL_FILE_NOT_FOUND")


@router.get("/{document_id}/original")
def get_original_document(document_id: str, db: Session = Depends(get_domain_db)) -> FileResponse:
    item = db.get(EvidenceDocument, document_id)
    if item is None:
        raise HTTPException(status_code=404, detail="DOCUMENT_NOT_FOUND")
    path = _verified_original_path(item)
    return FileResponse(
        path=path,
        media_type=item.mime_type or "application/octet-stream",
        filename=item.original_filename or path.name,
        content_disposition_type="inline",
        headers={
            "Cache-Control": "no-store",
            "X-Content-Type-Options": "nosniff",
            "X-CREED-Content-SHA256": item.content_hash,
            "X-CREED-Original-Verified": "true",
        },
    )


@router.post("", response_model=DocumentDetail, status_code=201)
async def upload_document(
    file: UploadFile = File(...),
    source: str = Form(default="LOCAL_DEMO"),
    title: str | None = Form(default=None),
    version: str | None = Form(default=None),
    issue_id: str | None = Form(default=None),
    db: Session = Depends(get_domain_db),
) -> DocumentDetail:
    settings = get_settings()
    filename = file.filename or ""
    try:
        data = await file.read(settings.max_document_bytes + 1)
        if len(data) > settings.max_document_bytes:
            raise HTTPException(status_code=413, detail="FILE_TOO_LARGE")
        parsed = parse_document(filename, data, declared_content_type=file.content_type)
    except DocumentIngestionError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    finally:
        await file.close()

    source_clean = source.strip().upper() or "LOCAL_DEMO"
    if issue_id and db.get(SupportIssue, issue_id) is None:
        raise HTTPException(status_code=422, detail="ISSUE_NOT_FOUND")
    existing = db.scalar(
        select(EvidenceDocument).where(
            EvidenceDocument.source == source_clean,
            EvidenceDocument.content_hash == parsed.content_hash,
        )
    )
    if existing is not None:
        if issue_id:
            existing_link = db.scalar(
                select(IssueEvidenceLink).where(
                    IssueEvidenceLink.issue_id == issue_id,
                    IssueEvidenceLink.document_id == existing.id,
                )
            )
            if existing_link is None:
                db.add(
                    IssueEvidenceLink(
                        issue_id=issue_id,
                        document_id=existing.id,
                        link_type="ATTACHMENT",
                    )
                )
                db.add(
                    AuditEvent(
                        actor="demo-operator",
                        action="ISSUE_EVIDENCE_LINKED",
                        object_type="SupportIssue",
                        object_id=issue_id,
                        metadata_json={"document_id": existing.id, "reused_existing_document": True},
                    )
                )
                db.commit()
            base = to_read(existing).model_dump()
            return DocumentDetail(**base, extracted_text=existing.extracted_text or "")
        raise HTTPException(status_code=409, detail={"code": "DUPLICATE_DOCUMENT", "document_id": existing.id})

    document_id = uuid_str()
    storage_root = settings.document_storage_dir
    try:
        stored_path = persist_file(storage_root, document_id, parsed.original_filename, data)
    except FileExistsError as exc:
        raise HTTPException(status_code=409, detail="DOCUMENT_STORAGE_COLLISION") from exc
    except OSError as exc:
        raise HTTPException(status_code=503, detail=f"DOCUMENT_STORAGE_UNAVAILABLE: {exc.__class__.__name__}") from exc

    item = EvidenceDocument(
        id=document_id,
        source=source_clean,
        title=(title or parsed.title).strip()[:300],
        document_type=parsed.document_type,
        version=version.strip()[:80] if version and version.strip() else None,
        content_hash=parsed.content_hash,
        original_filename=parsed.original_filename,
        mime_type=parsed.mime_type,
        file_size=parsed.file_size,
        storage_path=str(stored_path),
        parse_status="PARSED",
        parse_error=None,
        extracted_text=parsed.text,
        char_count=len(parsed.text),
        metadata_json={"knowledge_mode": "LOCAL_DEMO", "parser": "CREED_M04"},
        index_status="PENDING",
    )
    audit = AuditEvent(
        actor="api-user",
        action="DOCUMENT_INGESTED",
        object_type="EvidenceDocument",
        object_id=document_id,
        metadata_json={
            "source": source_clean,
            "document_type": parsed.document_type,
            "filename": parsed.original_filename,
            "content_hash": parsed.content_hash,
        },
    )
    issue_link = None
    issue_audit = None
    if issue_id:
        issue_link = IssueEvidenceLink(
            issue_id=issue_id,
            document_id=document_id,
            link_type="ATTACHMENT",
        )
        issue_audit = AuditEvent(
            actor="demo-operator",
            action="ISSUE_EVIDENCE_LINKED",
            object_type="SupportIssue",
            object_id=issue_id,
            metadata_json={"document_id": document_id, "reused_existing_document": False},
        )
    try:
        db.add_all([value for value in [item, audit, issue_link, issue_audit] if value is not None])
        db.commit()
        db.refresh(item)
    except SQLAlchemyError as exc:
        db.rollback()
        try:
            Path(stored_path).unlink(missing_ok=True)
            Path(stored_path).parent.rmdir()
        except OSError:
            pass
        raise HTTPException(status_code=503, detail=f"DATABASE_UNAVAILABLE: {exc.__class__.__name__}") from exc

    # M05 indexes immediately when possible. The configured local hashing fallback keeps
    # ingestion functional if the preferred Ollama embedding model is temporarily unavailable.
    try:
        RetrievalService().index_document(db, item)
        db.refresh(item)
    except Exception:
        db.rollback()
        item = db.get(EvidenceDocument, document_id) or item
        item.index_status = "PENDING"
        db.commit()
        db.refresh(item)

    base = to_read(item).model_dump()
    return DocumentDetail(**base, extracted_text=item.extracted_text or "")
