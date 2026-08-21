from __future__ import annotations

import json
import sqlite3
import threading
import time
import traceback
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, TypedDict

from sqlalchemy import create_engine, func, select
from sqlalchemy.orm import Session, sessionmaker, selectinload

from app.core.config import get_settings
from app.domain.enums import AgentStatus, IssueStatus
from app.domain.models import (
    AgentRun,
    AgentStep,
    AgentEvent,
    AuditEvent,
    Client,
    EvidenceDocument,
    Implementation,
    Investigation,
    InvestigationDetail,
    IssueEvidenceLink,
    IssueUnderstanding,
    Module,
    Product,
    SupportIssue,
    utc_now,
    uuid_str,
)
from app.services.issue_understanding import build_fast_issue_extraction, run_issue_understanding, should_use_fast_issue_understanding
from app.services.advanced import discover_evidence, investigations_for_run, resolve_catalog_context, resolve_method_versions_from_evidence, score_blast_radius, run_investigations


AGENT_SPECS: tuple[dict[str, Any], ...] = (
    {"name": "intake_agent", "display_name": "Intake Agent", "task": "Understand the saved issue", "sequence": 10, "module": "M07/M08"},
    {"name": "retrieval_agent", "display_name": "Retrieval Agent", "task": "Search FSDs, tests and project evidence", "sequence": 20, "module": "M09"},
    {"name": "knowledge_link_agent", "display_name": "Knowledge Link Agent", "task": "Resolve delivery methods and dependencies", "sequence": 30, "module": "M10"},
    {"name": "impact_agent", "display_name": "Impact Agent", "task": "Calculate explainable blast radius", "sequence": 40, "module": "M11"},
    {"name": "investigation_agent", "display_name": "Investigation Agent", "task": "Investigate candidate implementation evidence", "sequence": 50, "module": "M12"},
    {"name": "evidence_validator", "display_name": "Evidence Validator", "task": "Validate finding evidence references", "sequence": 60, "module": "M12"},
    {"name": "human_review_boundary", "display_name": "Human Review", "task": "Pause for human review and authority", "sequence": 70, "module": "M13"},
)

TERMINAL_RUN_STATUSES = {AgentStatus.COMPLETED.value, AgentStatus.FAILED.value, AgentStatus.CANCELLED.value}


class CreedAnalysisState(TypedDict, total=False):
    run_id: str
    issue_id: str
    raw_issue: str
    issue_capsule: dict[str, Any]
    search_queries: list[str]
    retrieved_evidence: list[dict[str, Any]]
    related_methods: list[dict[str, Any]]
    knowledge_context: dict[str, Any]
    candidate_implementations: list[dict[str, Any]]
    impact_results: list[dict[str, Any]]
    investigations: list[dict[str, Any]]
    findings: list[dict[str, Any]]
    evidence_gaps: list[str]
    human_decision: dict[str, Any] | None
    review_boundary: str | None
    agent_statuses: dict[str, str]
    errors: list[str]


def _factory(database_url: str) -> sessionmaker[Session]:
    connect_args: dict[str, object] = {}
    if database_url.startswith("sqlite"):
        connect_args["check_same_thread"] = False
    engine = create_engine(database_url, pool_pre_ping=True, connect_args=connect_args)
    return sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


def langgraph_runtime_available() -> tuple[bool, str | None]:
    try:
        import langgraph  # noqa: F401
        from langgraph.checkpoint.sqlite import SqliteSaver  # noqa: F401
        return True, None
    except Exception as exc:  # Import failure must be visible, never papered over.
        return False, f"{exc.__class__.__name__}: {exc}"


def _checkpoint_path(database_url: str) -> Path:
    settings = get_settings()
    if database_url.startswith("sqlite:///") and ":memory:" not in database_url:
        db_path = Path(database_url.removeprefix("sqlite:///"))
        return db_path.with_name(f"{db_path.stem}.langgraph-checkpoints.sqlite")
    return Path(settings.langgraph_checkpoint_path)


def analysis_run_recovery_status(db: Session, run: AgentRun) -> tuple[bool, str | None]:
    """Return whether a persisted WAITING_HUMAN run is a safe zero-case recovery candidate.

    Recovery is intentionally narrow: it is only allowed when the run is waiting at Human Review
    but no investigation records were persisted for the issue. This prevents the recovery action
    from bypassing a real governed Human Decision boundary.
    """
    if run.status != AgentStatus.WAITING_HUMAN.value:
        return False, "RUN_NOT_WAITING_HUMAN"
    if not run.issue_id:
        return False, "RUN_HAS_NO_ISSUE"
    issue_investigations = len(investigations_for_run(db, run.id))
    run_details = db.scalar(
        select(func.count()).select_from(InvestigationDetail).where(InvestigationDetail.agent_run_id == run.id)
    ) or 0
    if int(issue_investigations) > 0 or int(run_details) > 0:
        return False, "HUMAN_REVIEW_CASES_EXIST"
    step = db.scalar(
        select(AgentStep).where(
            AgentStep.agent_run_id == run.id,
            AgentStep.agent_name == "human_review_boundary",
        )
    )
    if step is None or step.status != AgentStatus.WAITING_HUMAN.value:
        return False, "HUMAN_REVIEW_CHECKPOINT_NOT_STALE"
    return True, "STALE_ZERO_CASE_HUMAN_REVIEW"


def supersede_stuck_analysis_run(
    db: Session,
    run: AgentRun,
    *,
    reason: str,
    actor: str = "demo-operator",
) -> None:
    eligible, code = analysis_run_recovery_status(db, run)
    if not eligible:
        raise ValueError(code or "ANALYSIS_RUN_NOT_RECOVERABLE")
    now = utc_now()
    run.status = AgentStatus.CANCELLED.value
    run.completed_at = now
    run.output_summary = "Superseded by controlled zero-case recovery; prior audit and checkpoint retained"
    for step in db.scalars(select(AgentStep).where(AgentStep.agent_run_id == run.id)).all():
        if step.status in {AgentStatus.QUEUED.value, AgentStatus.RUNNING.value, AgentStatus.WAITING_HUMAN.value}:
            step.status = AgentStatus.CANCELLED.value
            step.completed_at = now
            if step.agent_name == "human_review_boundary":
                step.output_summary = "Stale zero-case Human Review checkpoint superseded by controlled recovery"
                current = dict(step.metadata_json or {})
                current.update({
                    "recovery_superseded": True,
                    "recovery_reason": reason,
                    "review_case_count": 0,
                })
                step.metadata_json = current
                _append_agent_event(
                    db,
                    run_db_id=run.id,
                    step=step,
                    agent_name=step.agent_name,
                    status=AgentStatus.CANCELLED.value,
                    message=step.output_summary,
                    metadata={
                        "recovery_superseded": True,
                        "review_case_count": 0,
                        "reason": reason,
                    },
                )
    if run.issue_id and (issue := db.get(SupportIssue, run.issue_id)):
        issue.status = IssueStatus.OPEN.value
    db.add(
        AuditEvent(
            actor=actor,
            action="ANALYSIS_RUN_RECOVERY_SUPERSEDED",
            object_type="AgentRun",
            object_id=run.id,
            metadata_json={
                "graph_run_id": run.graph_run_id,
                "issue_id": run.issue_id,
                "reason": reason,
                "preserved_history": True,
                "preserved_checkpoint": True,
                "review_case_count": 0,
            },
        )
    )
    db.commit()


def create_analysis_run(db: Session, issue: SupportIssue) -> AgentRun:
    graph_run_id = f"CREED-{datetime.now(timezone.utc).strftime('%Y%m%d')}-{uuid.uuid4().hex[:10].upper()}"
    run = AgentRun(
        id=uuid_str(),
        graph_run_id=graph_run_id,
        issue_id=issue.id,
        status=AgentStatus.QUEUED.value,
        input_summary=issue.title,
    )
    db.add(run)
    db.flush()
    for spec in AGENT_SPECS:
        step = AgentStep(
            id=uuid_str(),
            agent_run_id=run.id,
            agent_name=spec["name"],
            status=AgentStatus.QUEUED.value,
            sequence=spec["sequence"],
            input_summary=spec["task"],
            metadata_json={
                "display_name": spec["display_name"],
                "module": spec["module"],
                "task": spec["task"],
                "runtime_source": "LANGGRAPH_NODE",
            },
        )
        db.add(step)
        db.flush()
        _append_agent_event(
            db, run_db_id=run.id, step=step, agent_name=spec["name"], status=AgentStatus.QUEUED.value,
            message=f"{spec['display_name']} queued", metadata={"sequence": spec["sequence"], "module": spec["module"]},
        )
    issue.status = IssueStatus.ANALYSING.value
    db.add(
        AuditEvent(
            actor="demo-operator",
            action="ANALYSIS_RUN_QUEUED",
            object_type="AgentRun",
            object_id=run.id,
            metadata_json={"graph_run_id": graph_run_id, "issue_id": issue.id},
        )
    )
    db.commit()
    db.refresh(run)
    return run



def _append_agent_event(
    db: Session,
    *,
    run_db_id: str,
    step: AgentStep | None,
    agent_name: str,
    status: str,
    message: str | None = None,
    metadata: dict[str, Any] | None = None,
) -> AgentEvent:
    from sqlalchemy import func
    latest = db.scalar(select(func.max(AgentEvent.event_seq)).where(AgentEvent.agent_run_id == run_db_id)) or 0
    event = AgentEvent(
        id=uuid_str(),
        agent_run_id=run_db_id,
        agent_step_id=step.id if step else None,
        event_seq=int(latest) + 1,
        agent_name=agent_name,
        status=status,
        message=message,
        metadata_json=metadata or {},
    )
    db.add(event)
    return event

def _get_step(db: Session, run_db_id: str, agent_name: str) -> AgentStep:
    step = db.scalar(select(AgentStep).where(AgentStep.agent_run_id == run_db_id, AgentStep.agent_name == agent_name))
    if step is None:
        raise RuntimeError(f"AGENT_STEP_NOT_FOUND:{agent_name}")
    return step


def _mark_step_running(factory: sessionmaker[Session], run_db_id: str, agent_name: str) -> None:
    with factory() as db:
        step = _get_step(db, run_db_id, agent_name)
        step.status = AgentStatus.RUNNING.value
        step.started_at = utc_now()
        step.completed_at = None
        step.error = None
        run = db.get(AgentRun, run_db_id)
        if run:
            run.status = AgentStatus.RUNNING.value
            run.started_at = run.started_at or utc_now()
        _append_agent_event(
            db, run_db_id=run_db_id, step=step, agent_name=agent_name, status=AgentStatus.RUNNING.value,
            message=f"{(step.metadata_json or {}).get('display_name', agent_name)} running",
        )
        db.commit()


def _mark_step_completed(
    factory: sessionmaker[Session],
    run_db_id: str,
    agent_name: str,
    *,
    output_summary: str,
    metadata: dict[str, Any] | None = None,
    skipped: bool = False,
) -> None:
    with factory() as db:
        step = _get_step(db, run_db_id, agent_name)
        step.status = AgentStatus.SKIPPED.value if skipped else AgentStatus.COMPLETED.value
        step.completed_at = utc_now()
        step.output_summary = output_summary
        current = dict(step.metadata_json or {})
        current.update(metadata or {})
        step.metadata_json = current
        final_status = AgentStatus.SKIPPED.value if skipped else AgentStatus.COMPLETED.value
        _append_agent_event(
            db, run_db_id=run_db_id, step=step, agent_name=agent_name, status=final_status,
            message=output_summary, metadata=metadata or {},
        )
        db.commit()


def _mark_step_failed(factory: sessionmaker[Session], run_db_id: str, agent_name: str, exc: Exception) -> None:
    with factory() as db:
        step = _get_step(db, run_db_id, agent_name)
        step.status = AgentStatus.FAILED.value
        step.completed_at = utc_now()
        step.error = f"{exc.__class__.__name__}: {exc}"[:2000]
        run = db.get(AgentRun, run_db_id)
        if run:
            run.status = AgentStatus.FAILED.value
            run.completed_at = utc_now()
            run.error = step.error
        if run and run.issue_id:
            issue = db.get(SupportIssue, run.issue_id)
            if issue:
                issue.status = IssueStatus.OPEN.value
        _append_agent_event(
            db, run_db_id=run_db_id, step=step, agent_name=agent_name, status=AgentStatus.FAILED.value,
            message=step.error, metadata={"error": step.error},
        )
        db.add(
            AuditEvent(
                actor="creed-langgraph",
                action="ANALYSIS_RUN_FAILED",
                object_type="AgentRun",
                object_id=run_db_id,
                metadata_json={"agent_name": agent_name, "error": step.error},
            )
        )
        db.commit()


def _instrument(
    factory: sessionmaker[Session],
    run_db_id: str,
    agent_name: str,
    fn: Callable[[CreedAnalysisState], CreedAnalysisState],
) -> Callable[[CreedAnalysisState], CreedAnalysisState]:
    def wrapped(state: CreedAnalysisState) -> CreedAnalysisState:
        _mark_step_running(factory, run_db_id, agent_name)
        try:
            result = fn(state)
            result = dict(result)
            summary = str(result.pop("_step_summary", f"{agent_name} completed"))
            metadata = dict(result.pop("_step_metadata", {}))
            skipped = bool(result.pop("_step_skipped", False))
            _mark_step_completed(factory, run_db_id, agent_name, output_summary=summary, metadata=metadata, skipped=skipped)
            return result  # type: ignore[return-value]
        except Exception as exc:
            from langgraph.errors import GraphInterrupt

            if isinstance(exc, GraphInterrupt):
                raise
            _mark_step_failed(factory, run_db_id, agent_name, exc)
            raise
    return wrapped


def _intake_node(factory: sessionmaker[Session], issue_id: str) -> Callable[[CreedAnalysisState], CreedAnalysisState]:
    def node(state: CreedAnalysisState) -> CreedAnalysisState:
        with factory() as db:
            issue = db.scalar(
                select(SupportIssue)
                .where(SupportIssue.id == issue_id)
                .options(selectinload(SupportIssue.client))
            )
            if issue is None:
                raise RuntimeError("ISSUE_NOT_FOUND")
            understanding = db.scalar(
                select(IssueUnderstanding)
                .where(IssueUnderstanding.issue_id == issue_id)
                .order_by(IssueUnderstanding.created_at.desc())
                .limit(1)
            )
            reused = understanding is not None
            fast_generated = False
            if understanding is None and should_use_fast_issue_understanding(issue):
                extracted = build_fast_issue_extraction(issue)
                fast_generated = True
                capsule = {
                    "understanding_id": None,
                    "client": extracted.client,
                    "product": extracted.product,
                    "module": extracted.module,
                    "issue_type": extracted.issue_type,
                    "summary": extracted.summary,
                    "suspected_function": extracted.suspected_function,
                    "keywords": list(extracted.keywords),
                    "severity": extracted.severity,
                    "confidence": extracted.confidence,
                    "model": "FAST_RULES",
                    "human_verified": False,
                }
                query_terms = [x for x in [extracted.product, extracted.module, extracted.suspected_function, *list(extracted.keywords)] if x]
            else:
                if understanding is None:
                    understanding = run_issue_understanding(db, issue)
                capsule = {
                    "understanding_id": understanding.id,
                    "client": understanding.client_name,
                    "product": understanding.product,
                    "module": understanding.module,
                    "issue_type": understanding.issue_type,
                    "summary": understanding.summary,
                    "suspected_function": understanding.suspected_function,
                    "keywords": list(understanding.keywords_json or []),
                    "severity": understanding.severity,
                    "confidence": understanding.confidence,
                    "model": understanding.actual_model or understanding.configured_model,
                    "human_verified": understanding.status == "HUMAN_VERIFIED",
                }
                query_terms = [x for x in [understanding.product, understanding.module, understanding.suspected_function, *list(understanding.keywords_json or [])] if x]
            return {
                "issue_capsule": capsule,
                "search_queries": list(dict.fromkeys(query_terms))[:8],
                "_step_summary": f"{'Reused' if reused else 'Generated'} structured issue understanding · {len(query_terms)} search concepts",
                "_step_metadata": {
                    "model_used": capsule["model"],
                    "understanding_id": understanding.id if understanding is not None else None,
                    "confidence": capsule["confidence"],
                    "reused_existing_understanding": reused,
                    "fast_path_used": fast_generated,
                },
            }
    return node


def _retrieval_node(factory: sessionmaker[Session], issue_id: str, run_db_id: str) -> Callable[[CreedAnalysisState], CreedAnalysisState]:
    def node(state: CreedAnalysisState) -> CreedAnalysisState:
        with factory() as db:
            run=db.get(AgentRun,run_db_id)
            if not run: raise RuntimeError("ANALYSIS_RUN_NOT_FOUND")
            result=discover_evidence(db,run)
            return {
                "retrieved_evidence": result["results"],
                "search_queries": result["queries"],
                "_step_summary": f"{result['result_count']} relevant evidence item(s) found · {result['searched_chunks']} chunks searched",
                "_step_metadata": {"evidence_count":result["result_count"],"searched_chunks":result["searched_chunks"],"queries":result["queries"]},
            }
    return node


def _knowledge_link_node(factory: sessionmaker[Session], run_db_id: str) -> Callable[[CreedAnalysisState], CreedAnalysisState]:
    def node(state: CreedAnalysisState) -> CreedAnalysisState:
        capsule=state.get("issue_capsule") or {}; context={"product_id":None,"module_id":None,"match":"NONE"}
        with factory() as db:
            run=db.get(AgentRun,run_db_id)
            resolved=resolve_catalog_context(db,run.issue_id) if run and run.issue_id else {"product":None,"module":None,"product_strategy":"NONE","module_strategy":"NONE"}
            product=resolved.get("product")
            module=resolved.get("module")
            if product:context["product_id"]=product.id
            if module:context["module_id"]=module.id
            context["match"]=resolved.get("module_strategy") if module else resolved.get("product_strategy") if product else "NONE"
            context["product_match"]=resolved.get("product_strategy")
            context["module_match"]=resolved.get("module_strategy")
            versions=resolve_method_versions_from_evidence(db,run_db_id)
            related=[{"id":v.id,"version":v.version,"status":v.status,"method_id":v.method_id} for v in versions]
            return {"knowledge_context":context,"related_methods":related,"_step_summary":f"Resolved {len(related)} delivery method version(s) from retrieved evidence · catalog {context['match']}","_step_metadata":{**context,"method_version_ids":[v.id for v in versions]}}
    return node


def _impact_node(factory: sessionmaker[Session], run_db_id: str) -> Callable[[CreedAnalysisState], CreedAnalysisState]:
    def node(state: CreedAnalysisState) -> CreedAnalysisState:
        with factory() as db:
            run=db.get(AgentRun,run_db_id)
            if not run: raise RuntimeError("ANALYSIS_RUN_NOT_FOUND")
            result=score_blast_radius(db,run)
            routing=result.get("routing") or {}
            candidates=[{"implementation_id":r["implementation_id"],"client_id":r["client_id"],"client_name":r["client_name"],"name":r["implementation_name"],"candidate_reason":"USES_RELATED_METHOD_VERSION" if r["method_version_id"] else routing.get("strategy","CATALOG_MODULE_MATCH")} for r in result["results"]]
            return {"candidate_implementations":candidates,"impact_results":result["results"],"_step_summary":f"Scored {len(candidates)} implementation(s) with explainable blast radius · {routing.get('strategy','UNKNOWN')}","_step_metadata":{"candidate_count":len(candidates),"scoring_performed":True,"routing":routing}}
    return node


def _investigation_node(factory: sessionmaker[Session], run_db_id: str) -> Callable[[CreedAnalysisState], CreedAnalysisState]:
    def node(state: CreedAnalysisState) -> CreedAnalysisState:
        with factory() as db:
            run=db.get(AgentRun,run_db_id)
            if not run: raise RuntimeError("ANALYSIS_RUN_NOT_FOUND")
            result=run_investigations(db,run)
            return {"investigations":result["results"],"findings":result["results"],"_step_summary":f"Investigated {result['result_count']} implementation(s) against supplied evidence","_step_metadata":{"qwen_investigation_performed":True,"result_count":result["result_count"]}}
    return node


def _evidence_validator_node(state: CreedAnalysisState) -> CreedAnalysisState:
    gaps=[]
    for item in state.get("findings") or []:
        if item.get("finding_type")!="INSUFFICIENT_EVIDENCE" and not item.get("evidence_refs"):
            gaps.append(f"FINDING_WITHOUT_EVIDENCE:{item.get('investigation_id')}")
    return {"evidence_gaps":gaps,"_step_summary":"All supported findings retain evidence references" if not gaps else f"{len(gaps)} evidence validation gap(s)","_step_metadata":{"evidence_gap_count":len(gaps),"gaps":gaps}}


def _human_review_boundary_node(factory: sessionmaker[Session], run_db_id: str) -> Callable[[CreedAnalysisState], CreedAnalysisState]:
    def node(state: CreedAnalysisState) -> CreedAnalysisState:
        investigations = list(state.get("investigations") or [])
        if not investigations:
            with factory() as db:
                run = db.get(AgentRun, run_db_id)
                db.add(
                    AuditEvent(
                        actor="creed-langgraph",
                        action="HUMAN_REVIEW_SKIPPED_NO_CASES",
                        object_type="AgentRun",
                        object_id=run_db_id,
                        metadata_json={
                            "graph_run_id": run.graph_run_id if run else state.get("run_id"),
                            "reason": "NO_INVESTIGATION_CASES",
                            "review_case_count": 0,
                        },
                    )
                )
                db.commit()
            return {
                "review_boundary": "SKIPPED_NO_CASES",
                "_step_summary": "Human review skipped · no investigation cases persisted",
                "_step_metadata": {
                    "interrupt_executed": False,
                    "review_case_count": 0,
                    "skip_reason": "NO_INVESTIGATION_CASES",
                },
                "_step_skipped": True,
            }

        from langgraph.types import interrupt
        with factory() as db:
            run=db.get(AgentRun,run_db_id); step=_get_step(db,run_db_id,"human_review_boundary")
            if run:
                run.status=AgentStatus.WAITING_HUMAN.value
                if run.issue_id and (issue:=db.get(SupportIssue,run.issue_id)): issue.status=IssueStatus.WAITING_HUMAN.value
            step.status=AgentStatus.WAITING_HUMAN.value
            _append_agent_event(db,run_db_id=run_db_id,step=step,agent_name="human_review_boundary",status=AgentStatus.WAITING_HUMAN.value,message=f"Human review required for {len(investigations)} implementation(s)")
            db.commit()
        decision=interrupt({"graph_run_id":state.get("run_id"),"investigations":investigations,"allowed_decisions":["AFFECTED","NOT_AFFECTED","NEEDS_MORE_INVESTIGATION"]})
        return {"human_decision":decision,"review_boundary":"COMPLETED","_step_summary":"Human authority resumed the workflow","_step_metadata":{"interrupt_executed":True,"review_case_count":len(investigations)}}
    return node


def _build_graph(factory: sessionmaker[Session], run_db_id: str, issue_id: str, checkpointer: Any):
    # Lazy imports keep the API fail-closed if dependencies are unavailable rather than crashing all of CREED.
    from langgraph.graph import END, START, StateGraph

    builder = StateGraph(CreedAnalysisState)
    nodes: tuple[tuple[str, Callable[[CreedAnalysisState], CreedAnalysisState]], ...] = (
        ("intake_agent", _intake_node(factory, issue_id)),
        ("retrieval_agent", _retrieval_node(factory, issue_id, run_db_id)),
        ("knowledge_link_agent", _knowledge_link_node(factory, run_db_id)),
        ("impact_agent", _impact_node(factory, run_db_id)),
        ("investigation_agent", _investigation_node(factory, run_db_id)),
        ("evidence_validator", _evidence_validator_node),
        ("human_review_boundary", _human_review_boundary_node(factory, run_db_id)),
    )
    for name, fn in nodes:
        builder.add_node(name, _instrument(factory, run_db_id, name, fn))
    builder.add_edge(START, "intake_agent")
    for (left, _), (right, _) in zip(nodes, nodes[1:]):
        builder.add_edge(left, right)
    builder.add_edge("human_review_boundary", END)
    return builder.compile(checkpointer=checkpointer)


def execute_analysis_run(*, run_db_id: str, database_url: str) -> None:
    available, reason = langgraph_runtime_available()
    factory = _factory(database_url)
    if not available:
        exc = RuntimeError(f"LANGGRAPH_RUNTIME_UNAVAILABLE: {reason}")
        _mark_run_boot_failure(factory, run_db_id, exc)
        return

    from langgraph.checkpoint.sqlite import SqliteSaver

    with factory() as db:
        run = db.get(AgentRun, run_db_id)
        if run is None or run.issue_id is None:
            return
        issue_id = run.issue_id
        graph_run_id = run.graph_run_id

    path = _checkpoint_path(database_url)
    path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(path, check_same_thread=False)
    try:
        checkpointer = SqliteSaver(connection)
        graph = _build_graph(factory, run_db_id, issue_id, checkpointer)
        config = {"configurable": {"thread_id": graph_run_id}}
        initial: CreedAnalysisState = {
            "run_id": graph_run_id,
            "issue_id": issue_id,
            "raw_issue": "",
            "issue_capsule": {},
            "search_queries": [],
            "retrieved_evidence": [],
            "related_methods": [],
            "candidate_implementations": [],
            "impact_results": [],
            "investigations": [],
            "findings": [],
            "evidence_gaps": [],
            "human_decision": None,
            "agent_statuses": {},
            "errors": [],
        }
        result = graph.invoke(initial, config=config, durability="sync")
        # Prove the state is retrievable from the checkpointer after execution.
        snapshot = graph.get_state(config)
        checkpoint_id = (snapshot.config or {}).get("configurable", {}).get("checkpoint_id") if snapshot else None
        with factory() as db:
            run = db.get(AgentRun, run_db_id)
            interrupted = bool(snapshot and getattr(snapshot, "next", None))
            no_review_cases = result.get("review_boundary") == "SKIPPED_NO_CASES"
            candidate_count = len(result.get("candidate_implementations", []))
            investigation_count = len(result.get("investigations", []))
            if run and interrupted:
                run.status = AgentStatus.WAITING_HUMAN.value
                run.output_summary = "AI investigation complete · waiting for human review"
            elif run:
                run.status = AgentStatus.COMPLETED.value
                run.completed_at = utc_now()
                if no_review_cases:
                    if candidate_count == 0:
                        run.output_summary = "CREED analysis completed · no candidate implementations found · human review skipped"
                    else:
                        run.output_summary = "CREED analysis completed · no investigation cases persisted · human review skipped"
                else:
                    run.output_summary = f"CREED analysis completed · {candidate_count} implementation(s) assessed"
            issue = db.get(SupportIssue, issue_id)
            if issue:
                if interrupted:
                    issue.status = IssueStatus.WAITING_HUMAN.value
                elif no_review_cases:
                    # A zero-case analysis is terminal as a graph run, but the issue remains open so
                    # an operator can correct evidence/routing and start a new real analysis run.
                    issue.status = IssueStatus.OPEN.value
                else:
                    issue.status = IssueStatus.RESOLVED.value
            db.add(
                AuditEvent(
                    actor="creed-langgraph",
                    action=(
                        "HUMAN_REVIEW_CHECKPOINT_SAVED"
                        if interrupted
                        else "ANALYSIS_RUN_NO_REVIEW_CASES"
                        if no_review_cases
                        else "ANALYSIS_RUN_COMPLETED"
                    ),
                    object_type="AgentRun",
                    object_id=run_db_id,
                    metadata_json={
                        "graph_run_id": graph_run_id,
                        "checkpoint_backend": "SQLITE",
                        "checkpoint_path": str(path),
                        "checkpoint_id": checkpoint_id,
                        "candidate_count": candidate_count,
                        "investigation_count": investigation_count,
                        "human_review_skipped": no_review_cases,
                    },
                )
            )
            db.commit()
    except Exception as exc:
        # A node wrapper already marks node failures. This catches graph/checkpointer failures before/after node execution.
        _mark_run_boot_failure(factory, run_db_id, exc)
    finally:
        connection.close()


def _mark_run_boot_failure(factory: sessionmaker[Session], run_db_id: str, exc: Exception) -> None:
    with factory() as db:
        run = db.get(AgentRun, run_db_id)
        if run is None:
            return
        already_failed = run.status == AgentStatus.FAILED.value
        if not already_failed:
            run.status = AgentStatus.FAILED.value
            run.completed_at = utc_now()
            run.error = f"{exc.__class__.__name__}: {exc}"[:2000]
            queued = db.scalars(select(AgentStep).where(AgentStep.agent_run_id == run_db_id, AgentStep.status == AgentStatus.QUEUED.value)).all()
            if queued:
                first = sorted(queued, key=lambda step: step.sequence)[0]
                first.status = AgentStatus.FAILED.value
                first.started_at = first.started_at or utc_now()
                first.completed_at = utc_now()
                first.error = run.error
                _append_agent_event(
                    db, run_db_id=run_db_id, step=first, agent_name=first.agent_name, status=AgentStatus.FAILED.value,
                    message=run.error, metadata={"bootstrap_failure": True},
                )
        if run.issue_id:
            issue = db.get(SupportIssue, run.issue_id)
            if issue:
                issue.status = IssueStatus.OPEN.value
        db.add(
            AuditEvent(
                actor="creed-langgraph",
                action="ANALYSIS_RUN_FAILED",
                object_type="AgentRun",
                object_id=run.id,
                metadata_json={"graph_run_id": run.graph_run_id, "error": run.error, "trace": traceback.format_exc(limit=3)},
            )
        )
        db.commit()


def resume_analysis_run(*, run_db_id: str, database_url: str, resume_payload: dict[str, Any]) -> dict[str, Any]:
    available, reason = langgraph_runtime_available()
    if not available: raise RuntimeError(f"LANGGRAPH_RUNTIME_UNAVAILABLE: {reason}")
    from langgraph.checkpoint.sqlite import SqliteSaver
    from langgraph.types import Command
    factory=_factory(database_url)
    with factory() as db:
        run=db.get(AgentRun,run_db_id)
        if not run or not run.issue_id: raise RuntimeError("ANALYSIS_RUN_NOT_FOUND")
        issue_id=run.issue_id; graph_run_id=run.graph_run_id
        run.status=AgentStatus.RUNNING.value
        db.commit()
    path=_checkpoint_path(database_url); path.parent.mkdir(parents=True,exist_ok=True); connection=sqlite3.connect(path,check_same_thread=False)
    try:
        graph=_build_graph(factory,run_db_id,issue_id,SqliteSaver(connection)); config={"configurable":{"thread_id":graph_run_id}}
        result=graph.invoke(Command(resume=resume_payload),config=config,durability="sync"); snapshot=graph.get_state(config)
        interrupted=bool(snapshot and getattr(snapshot,"next",None))
        with factory() as db:
            run=db.get(AgentRun,run_db_id); issue=db.get(SupportIssue,issue_id)
            if run:
                run.status=AgentStatus.WAITING_HUMAN.value if interrupted else AgentStatus.COMPLETED.value
                run.completed_at=None if interrupted else utc_now()
                run.output_summary="Additional investigation requires human review" if interrupted else "Human-reviewed CREED analysis completed"
            if issue: issue.status=IssueStatus.WAITING_HUMAN.value if interrupted else IssueStatus.RESOLVED.value
            db.add(AuditEvent(actor="creed-langgraph",action="HUMAN_REVIEW_RESUMED",object_type="AgentRun",object_id=run_db_id,metadata_json={"graph_run_id":graph_run_id,"interrupted_again":interrupted}))
            db.commit()
        return {"graph_run_id":graph_run_id,"status":AgentStatus.WAITING_HUMAN.value if interrupted else AgentStatus.COMPLETED.value,"result":result}
    finally:
        connection.close()


def launch_analysis_run(*, run_db_id: str, database_url: str) -> threading.Thread:
    thread = threading.Thread(
        target=execute_analysis_run,
        kwargs={"run_db_id": run_db_id, "database_url": database_url},
        name=f"creed-analysis-{run_db_id[:8]}",
        daemon=True,
    )
    thread.start()
    return thread


def serialize_analysis_run(db: Session, run: AgentRun) -> dict[str, Any]:
    steps = db.scalars(
        select(AgentStep).where(AgentStep.agent_run_id == run.id).order_by(AgentStep.sequence)
    ).all()
    now = utc_now()
    from sqlalchemy import func
    latest_event_seq = db.scalar(select(func.max(AgentEvent.event_seq)).where(AgentEvent.agent_run_id == run.id)) or 0
    return {
        "id": run.id,
        "graph_run_id": run.graph_run_id,
        "issue_id": run.issue_id,
        "status": run.status,
        "started_at": run.started_at.isoformat() if run.started_at else None,
        "completed_at": run.completed_at.isoformat() if run.completed_at else None,
        "input_summary": run.input_summary,
        "output_summary": run.output_summary,
        "error": run.error,
        "created_at": run.created_at.isoformat(),
        "checkpoint_backend": "SQLITE",
        "latest_event_seq": int(latest_event_seq),
        "recovery_eligible": analysis_run_recovery_status(db, run)[0],
        "recovery_reason": analysis_run_recovery_status(db, run)[1],
        "steps": [
            {
                "id": step.id,
                "agent_name": step.agent_name,
                "display_name": (step.metadata_json or {}).get("display_name", step.agent_name),
                "task": (step.metadata_json or {}).get("task", step.input_summary),
                "module": (step.metadata_json or {}).get("module"),
                "status": step.status,
                "sequence": step.sequence,
                "started_at": step.started_at.isoformat() if step.started_at else None,
                "completed_at": step.completed_at.isoformat() if step.completed_at else None,
                "duration_ms": _duration_ms(step.started_at, step.completed_at or (now if step.status == AgentStatus.RUNNING.value else None)),
                "output_summary": step.output_summary,
                "error": step.error,
                "metadata": step.metadata_json or {},
            }
            for step in steps
        ],
    }


def _duration_ms(start: datetime | None, end: datetime | None) -> float | None:
    if not start or not end:
        return None
    # SQLite may return naive datetimes. Normalize them as UTC for deterministic display math.
    if start.tzinfo is None:
        start = start.replace(tzinfo=timezone.utc)
    if end.tzinfo is None:
        end = end.replace(tzinfo=timezone.utc)
    return max(0.0, (end - start).total_seconds() * 1000)


def snapshot_fingerprint(payload: dict[str, Any]) -> str:
    # RUNNING duration changes every poll; exclude it so SSE only emits meaningful lifecycle changes.
    stable = dict(payload)
    stable["steps"] = [
        {k: v for k, v in step.items() if k != "duration_ms"}
        for step in payload.get("steps", [])
    ]
    return json.dumps(stable, sort_keys=True, separators=(",", ":"), default=str)
