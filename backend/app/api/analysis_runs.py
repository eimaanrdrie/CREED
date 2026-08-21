from __future__ import annotations

import asyncio
import json
import time

from fastapi import APIRouter, Depends, HTTPException, Query, Header
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session, selectinload

from app.api.domain import get_domain_db
from app.core.config import get_settings
from app.domain.models import AgentEvent, AgentRun, AuditEvent, SupportIssue
from app.services.analysis_runs import (
    TERMINAL_RUN_STATUSES,
    analysis_run_recovery_status,
    create_analysis_run,
    langgraph_runtime_available,
    launch_analysis_run,
    serialize_analysis_run,
    supersede_stuck_analysis_run,
    snapshot_fingerprint,
)

router = APIRouter(tags=["analysis-runs"])


class AnalysisStepRead(BaseModel):
    id: str
    agent_name: str
    display_name: str
    task: str | None
    module: str | None
    status: str
    sequence: int
    started_at: str | None
    completed_at: str | None
    duration_ms: float | None
    output_summary: str | None
    error: str | None
    metadata: dict


class AnalysisRunRead(BaseModel):
    id: str
    graph_run_id: str
    issue_id: str | None
    status: str
    started_at: str | None
    completed_at: str | None
    input_summary: str | None
    output_summary: str | None
    error: str | None
    created_at: str
    checkpoint_backend: str
    latest_event_seq: int
    recovery_eligible: bool = False
    recovery_reason: str | None = None
    steps: list[AnalysisStepRead]


class AnalysisRecoveryRequest(BaseModel):
    reason: str = Field(min_length=3, max_length=1000)


def _get_run_by_graph_id(db: Session, graph_run_id: str) -> AgentRun:
    run = db.scalar(select(AgentRun).where(AgentRun.graph_run_id == graph_run_id))
    if run is None:
        raise HTTPException(status_code=404, detail="ANALYSIS_RUN_NOT_FOUND")
    return run


@router.post("/issues/{issue_id}/analysis-runs", response_model=AnalysisRunRead, status_code=202)
def start_analysis_run(issue_id: str, db: Session = Depends(get_domain_db)) -> AnalysisRunRead:
    available, reason = langgraph_runtime_available()
    if not available:
        raise HTTPException(status_code=503, detail=f"LANGGRAPH_RUNTIME_UNAVAILABLE: {reason}")
    issue = db.scalar(select(SupportIssue).where(SupportIssue.id == issue_id).options(selectinload(SupportIssue.client)))
    if issue is None:
        raise HTTPException(status_code=404, detail="ISSUE_NOT_FOUND")
    active = db.scalar(
        select(AgentRun)
        .where(AgentRun.issue_id == issue_id, AgentRun.status.in_(["QUEUED", "RUNNING", "WAITING_HUMAN"]))
        .order_by(AgentRun.created_at.desc())
        .limit(1)
    )
    if active:
        return AnalysisRunRead.model_validate(serialize_analysis_run(db, active))
    try:
        run = create_analysis_run(db, issue)
        database_url = db.get_bind().url.render_as_string(hide_password=False)
        launch_analysis_run(run_db_id=run.id, database_url=database_url)
        return AnalysisRunRead.model_validate(serialize_analysis_run(db, run))
    except SQLAlchemyError as exc:
        db.rollback()
        raise HTTPException(status_code=503, detail=f"DATABASE_UNAVAILABLE: {exc.__class__.__name__}") from exc


@router.post("/issues/{issue_id}/analysis-runs/recover", response_model=AnalysisRunRead, status_code=202)
def recover_stuck_analysis_run(
    issue_id: str,
    payload: AnalysisRecoveryRequest,
    db: Session = Depends(get_domain_db),
) -> AnalysisRunRead:
    available, reason = langgraph_runtime_available()
    if not available:
        raise HTTPException(status_code=503, detail=f"LANGGRAPH_RUNTIME_UNAVAILABLE: {reason}")
    issue = db.scalar(
        select(SupportIssue)
        .where(SupportIssue.id == issue_id)
        .options(selectinload(SupportIssue.client))
    )
    if issue is None:
        raise HTTPException(status_code=404, detail="ISSUE_NOT_FOUND")
    active = db.scalar(
        select(AgentRun)
        .where(AgentRun.issue_id == issue_id, AgentRun.status.in_(["QUEUED", "RUNNING", "WAITING_HUMAN"]))
        .order_by(AgentRun.created_at.desc())
        .limit(1)
    )
    if active is None:
        raise HTTPException(status_code=409, detail="NO_ACTIVE_ANALYSIS_RUN_TO_RECOVER")
    eligible, recovery_code = analysis_run_recovery_status(db, active)
    if not eligible:
        raise HTTPException(status_code=409, detail=recovery_code or "ANALYSIS_RUN_NOT_RECOVERABLE")
    old_run_id = active.id
    old_graph_run_id = active.graph_run_id
    try:
        supersede_stuck_analysis_run(db, active, reason=payload.reason)
        run = create_analysis_run(db, issue)
        db.add(
            AuditEvent(
                actor="demo-operator",
                action="ANALYSIS_RUN_RECOVERY_STARTED",
                object_type="AgentRun",
                object_id=run.id,
                metadata_json={
                    "issue_id": issue_id,
                    "previous_run_id": old_run_id,
                    "previous_graph_run_id": old_graph_run_id,
                    "new_graph_run_id": run.graph_run_id,
                    "reason": payload.reason,
                },
            )
        )
        db.commit()
        database_url = db.get_bind().url.render_as_string(hide_password=False)
        launch_analysis_run(run_db_id=run.id, database_url=database_url)
        return AnalysisRunRead.model_validate(serialize_analysis_run(db, run))
    except SQLAlchemyError as exc:
        db.rollback()
        raise HTTPException(status_code=503, detail=f"DATABASE_UNAVAILABLE: {exc.__class__.__name__}") from exc


@router.get("/issues/{issue_id}/analysis-runs/latest", response_model=AnalysisRunRead | None)
def latest_analysis_run(issue_id: str, db: Session = Depends(get_domain_db)) -> AnalysisRunRead | None:
    if db.get(SupportIssue, issue_id) is None:
        raise HTTPException(status_code=404, detail="ISSUE_NOT_FOUND")
    run = db.scalar(select(AgentRun).where(AgentRun.issue_id == issue_id).order_by(AgentRun.created_at.desc()).limit(1))
    return AnalysisRunRead.model_validate(serialize_analysis_run(db, run)) if run else None


@router.get("/analysis-runs/{graph_run_id}", response_model=AnalysisRunRead)
def get_analysis_run(graph_run_id: str, db: Session = Depends(get_domain_db)) -> AnalysisRunRead:
    run = _get_run_by_graph_id(db, graph_run_id)
    return AnalysisRunRead.model_validate(serialize_analysis_run(db, run))


@router.get("/analysis-runs/{graph_run_id}/events")
async def analysis_run_events(
    graph_run_id: str,
    after: int = Query(default=0, ge=0),
    last_event_id: str | None = Header(default=None, alias="Last-Event-ID"),
    db: Session = Depends(get_domain_db),
) -> StreamingResponse:
    # Validate before returning a stream so a typo gets a normal 404.
    initial_run = _get_run_by_graph_id(db, graph_run_id)
    database_url = db.get_bind().url.render_as_string(hide_password=False)
    settings = get_settings()
    run_db_id = initial_run.id
    if after == 0 and last_event_id:
        try:
            after = max(0, int(last_event_id))
        except ValueError:
            after = 0

    async def generate():
        from sqlalchemy import create_engine
        from sqlalchemy.orm import sessionmaker

        connect_args = {"check_same_thread": False} if database_url.startswith("sqlite") else {}
        engine = create_engine(database_url, pool_pre_ping=True, connect_args=connect_args)
        factory = sessionmaker(bind=engine, expire_on_commit=False)
        last_seq = after
        last_snapshot = None
        started = time.monotonic()
        try:
            while time.monotonic() - started < settings.analysis_event_max_seconds:
                with factory() as stream_db:
                    run = stream_db.get(AgentRun, run_db_id)
                    if run is None:
                        yield "event: error\ndata: {\"detail\":\"ANALYSIS_RUN_NOT_FOUND\"}\n\n"
                        return
                    events = stream_db.scalars(
                        select(AgentEvent)
                        .where(AgentEvent.agent_run_id == run_db_id, AgentEvent.event_seq > last_seq)
                        .order_by(AgentEvent.event_seq)
                    ).all()
                    payload = serialize_analysis_run(stream_db, run)
                for item in events:
                    last_seq = item.event_seq
                    event_payload = {
                        "event_seq": item.event_seq,
                        "agent_name": item.agent_name,
                        "status": item.status,
                        "message": item.message,
                        "metadata": item.metadata_json or {},
                        "created_at": item.created_at.isoformat(),
                    }
                    yield f"id: {item.event_seq}\nevent: agent_step\ndata: {json.dumps(event_payload, separators=(',', ':'))}\n\n"
                fingerprint = snapshot_fingerprint(payload)
                if fingerprint != last_snapshot:
                    last_snapshot = fingerprint
                    yield f"event: snapshot\ndata: {json.dumps(payload, separators=(',', ':'))}\n\n"
                if payload["status"] in TERMINAL_RUN_STATUSES:
                    yield f"event: terminal\ndata: {json.dumps({'status': payload['status'], 'latest_event_seq': last_seq})}\n\n"
                    return
                await asyncio.sleep(settings.analysis_event_poll_seconds)
            yield "event: timeout\ndata: {\"detail\":\"EVENT_STREAM_WINDOW_ENDED\"}\n\n"
        finally:
            engine.dispose()

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no", "Connection": "keep-alive"},
    )
