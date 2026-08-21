from __future__ import annotations

import hashlib
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from sqlalchemy import delete, func, select
from sqlalchemy.orm import Session

from app.core.ai_runtime import get_ollama_runtime
from app.core.config import get_settings
from app.domain.models import *
from app.services.advanced import create_edge
from app.services.retrieval import RetrievalService


DEMO_VERSION = "CREED-DEMO-1.1"
DOC_META = {
    "BRD-COL-088.md": ("BRD-COL-088", "BRD"),
    "FSD-COL-104.md": ("FSD-COL-104", "FSD"),
    "TC-COL-217.md": ("TC-COL-217", "TEST"),
    "CFG-ATLAS-PTP-01.md": ("CFG-ATLAS-PTP-01", "CONFIG"),
    "TEST-ATLAS-PTP-R1.md": ("TEST-ATLAS-PTP-R1", "TEST"),
    "CFG-MERIDIAN-PTP-04.md": ("CFG-MERIDIAN-PTP-04", "CONFIG"),
    "TEST-MERIDIAN-PTP-R1.md": ("TEST-MERIDIAN-PTP-R1", "TEST"),
    "CFG-NOVA-PTP-08.md": ("CFG-NOVA-PTP-08", "CONFIG"),
    "TEST-NOVA-PTP-R1.md": ("TEST-NOVA-PTP-R1", "TEST"),
    "CHANGE-PTP-2026-02.md": ("CHANGE-PTP-2026-02", "CHANGE"),
}


def _demo_dir() -> Path:
    return Path(__file__).resolve().parents[2] / "demo_data"


def _count(db: Session, model, *criteria) -> int:
    stmt = select(func.count()).select_from(model)
    if criteria:
        stmt = stmt.where(*criteria)
    return int(db.scalar(stmt) or 0)


def reset_demo(db: Session) -> dict[str, Any]:
    """Reset the destructive synthetic judging dataset to one deterministic baseline.

    M11 deliberately resets the governance/deployment/ownership rows too. The old reset
    left those tables behind, which meant a second rehearsal could look ready while using
    stale authorities or responsibilities from an earlier run.
    """
    for model in [
        RecallCase,
        RecallNoticeDetail,
        AdoptionReceiptDetail,
        LearningProposalDetail,
        MethodVersionLineage,
        InvestigationDetail,
        AnalysisImpactAssessment,
        AnalysisEvidenceHit,
        AgentEvent,
        AgentStep,
        HumanDecision,
        Finding,
        Investigation,
        AdoptionReceipt,
        LearningProposal,
        RecallNotice,
        AgentRun,
        IssueUnderstanding,
        IssueEvidenceLink,
        ResponsibilityAssignment,
        ImplementationDeployment,
        AuditEvent,
        DependencyEdge,
        DocumentChunk,
        SupportIssue,
        EvidenceDocument,
        Implementation,
        MethodVersion,
        DeliveryMethod,
        Module,
        Product,
        Client,
        HumanAuthority,
    ]:
        db.execute(delete(model))
    db.commit()

    clients = {
        name: Client(name=name, client_type="BANK" if "Finance" not in name else "FINANCIAL_INSTITUTION")
        for name in ["Atlas Bank", "Meridian Bank", "Nova Finance"]
    }
    product = Product(name="Collections", description="Synthetic collections platform for CREED demo")
    db.add_all([*clients.values(), product])
    db.flush()

    module = Module(product_id=product.id, name="Promise-to-Pay", description="Promise-to-Pay lifecycle and event handling")
    db.add(module)
    db.flush()

    method = DeliveryMethod(module_id=module.id, name="PTP Event Handling", description="Reusable delivery method for PTP event processing")
    db.add(method)
    db.flush()
    v1 = MethodVersion(method_id=method.id, version="PTP-EVENT-v1", status="APPROVED", summary="Baseline event processing method")
    db.add(v1)
    db.flush()

    impls = {
        "Atlas Bank": Implementation(client_id=clients["Atlas Bank"].id, product_id=product.id, module_id=module.id, name="Atlas PTP Implementation", release_version="R1"),
        "Meridian Bank": Implementation(client_id=clients["Meridian Bank"].id, product_id=product.id, module_id=module.id, name="Meridian PTP Implementation", release_version="R1"),
        "Nova Finance": Implementation(client_id=clients["Nova Finance"].id, product_id=product.id, module_id=module.id, name="Nova PTP Implementation", release_version="R1"),
    }
    db.add_all(impls.values())
    db.flush()

    docs: dict[str, EvidenceDocument] = {}
    retriever = RetrievalService()
    for filename, (title, doctype) in DOC_META.items():
        path = _demo_dir() / filename
        text = path.read_text(encoding="utf-8")
        raw = text.encode()
        content_hash = hashlib.sha256(raw).hexdigest()
        doc = EvidenceDocument(
            source="LOCAL_DEMO",
            source_url=None,
            title=title,
            document_type=doctype,
            version="1.0",
            content_hash=content_hash,
            original_filename=filename,
            mime_type="text/markdown",
            file_size=len(raw),
            storage_path=str(path),
            parse_status="PARSED",
            extracted_text=text,
            char_count=len(text),
            metadata_json={"dataset": DEMO_VERSION, "synthetic": True},
        )
        db.add(doc)
        db.flush()
        retriever.index_document(db, doc)
        docs[title] = doc

    # 11 explicit delivery relationships: 3 method uses + 2 method evidence + 3 configs + 3 tests.
    for name, impl in impls.items():
        cfg = docs[{"Atlas Bank": "CFG-ATLAS-PTP-01", "Meridian Bank": "CFG-MERIDIAN-PTP-04", "Nova Finance": "CFG-NOVA-PTP-08"}[name]]
        test = docs[{"Atlas Bank": "TEST-ATLAS-PTP-R1", "Meridian Bank": "TEST-MERIDIAN-PTP-R1", "Nova Finance": "TEST-NOVA-PTP-R1"}[name]]
        create_edge(db, source_type="Implementation", source_id=impl.id, target_type="MethodVersion", target_id=v1.id, relationship="USES_METHOD_VERSION", confidence=1.0, evidence_document_id=cfg.id)
        create_edge(db, source_type="Implementation", source_id=impl.id, target_type="EvidenceDocument", target_id=cfg.id, relationship="CONFIGURED_BY", confidence=1.0)
        create_edge(db, source_type="Implementation", source_id=impl.id, target_type="EvidenceDocument", target_id=test.id, relationship="SUPPORTED_BY", confidence=1.0)
    create_edge(db, source_type="MethodVersion", source_id=v1.id, target_type="EvidenceDocument", target_id=docs["FSD-COL-104"].id, relationship="SPECIFIED_BY", confidence=1.0)
    create_edge(db, source_type="MethodVersion", source_id=v1.id, target_type="EvidenceDocument", target_id=docs["TC-COL-217"].id, relationship="VALIDATED_BY", confidence=1.0)

    # R94 governed demo authorities. These values match the exact-data-entry runbook.
    authorities = {
        "aisha": HumanAuthority(
            principal="aisha.rahman@creed.example", display_name="Aisha Rahman", role_title="Transformation Assurance Lead",
            active=True, can_submit_human_decision=True, can_approve_learning=True, can_authorize_recall=True,
            metadata_json={"dataset": DEMO_VERSION, "synthetic": True},
        ),
        "daniel": HumanAuthority(
            principal="daniel.lim@creed.example", display_name="Daniel Lim", role_title="Collections QA Lead",
            active=True, can_submit_human_decision=True, can_approve_learning=False, can_authorize_recall=False,
            metadata_json={"dataset": DEMO_VERSION, "synthetic": True},
        ),
        "farah": HumanAuthority(
            principal="farah.ismail@creed.example", display_name="Farah Ismail", role_title="Collections Product Owner",
            active=True, can_submit_human_decision=False, can_approve_learning=False, can_authorize_recall=False,
            metadata_json={"dataset": DEMO_VERSION, "synthetic": True},
        ),
        "marcus": HumanAuthority(
            principal="marcus.tan@creed.example", display_name="Marcus Tan", role_title="Principal Solution Architect",
            active=True, can_submit_human_decision=False, can_approve_learning=True, can_authorize_recall=False,
            metadata_json={"dataset": DEMO_VERSION, "synthetic": True},
        ),
        "sofia": HumanAuthority(
            principal="sofia.lee@creed.example", display_name="Sofia Lee", role_title="Implementation Delivery Lead",
            active=True, can_submit_human_decision=False, can_approve_learning=False, can_authorize_recall=False,
            metadata_json={"dataset": DEMO_VERSION, "synthetic": True},
        ),
    }
    db.add_all(authorities.values())
    db.flush()

    # Three production deployment records make release provenance deterministic for judging.
    deployment_specs = [
        ("Atlas Bank", datetime(2026, 4, 8, 2, 0, tzinfo=timezone.utc), "REL-ATLAS-COL-R1", "CFG-ATLAS-PTP-01"),
        ("Meridian Bank", datetime(2026, 4, 10, 2, 0, tzinfo=timezone.utc), "REL-MERIDIAN-COL-R1", "CFG-MERIDIAN-PTP-04"),
        ("Nova Finance", datetime(2026, 4, 12, 2, 0, tzinfo=timezone.utc), "REL-NOVA-COL-R1", "CFG-NOVA-PTP-08"),
    ]
    for client_name, deployed_at, ref, evidence_title in deployment_specs:
        db.add(ImplementationDeployment(
            implementation_id=impls[client_name].id,
            environment="PRODUCTION",
            status="DEPLOYED",
            deployed_at=deployed_at,
            deployment_reference=ref,
            evidence_document_id=docs[evidence_title].id,
            notes=f"Synthetic initial production deployment for {client_name} Promise-to-Pay implementation.",
        ))

    # Ten responsibility assignments mirror the runbook and keep accountability separate from authority permissions.
    ownership_specs = [
        ("PRODUCT", product.id, "PRODUCT_OWNER", authorities["farah"].id, "Collections Product"),
        ("PRODUCT", product.id, "QA_OWNER", authorities["daniel"].id, "Collections Quality Engineering"),
        ("MODULE", module.id, "MODULE_OWNER", authorities["farah"].id, "Collections Product"),
        ("MODULE", module.id, "TECHNICAL_OWNER", authorities["marcus"].id, "Collections Architecture"),
        ("MODULE", module.id, "QA_OWNER", authorities["daniel"].id, "Collections Quality Engineering"),
        ("METHOD", method.id, "TECHNICAL_OWNER", authorities["marcus"].id, "Collections Architecture"),
        ("METHOD", method.id, "QA_OWNER", authorities["daniel"].id, "Collections Quality Engineering"),
        ("IMPLEMENTATION", impls["Atlas Bank"].id, "IMPLEMENTATION_LEAD", authorities["sofia"].id, "Client Delivery"),
        ("IMPLEMENTATION", impls["Meridian Bank"].id, "IMPLEMENTATION_LEAD", authorities["sofia"].id, "Client Delivery"),
        ("IMPLEMENTATION", impls["Nova Finance"].id, "IMPLEMENTATION_LEAD", authorities["sofia"].id, "Client Delivery"),
    ]
    db.add_all([
        ResponsibilityAssignment(scope_type=scope_type, scope_id=scope_id, responsibility_type=responsibility, authority_id=authority_id, team_name=team)
        for scope_type, scope_id, responsibility, authority_id, team in ownership_specs
    ])

    # Historical context only; no live Atlas issue is pre-seeded.
    db.add(SupportIssue(
        external_ticket_id="HIST-MER-001", client_id=clients["Meridian Bank"].id, title="Historical duplicate PTP replay",
        description="Duplicate PTP replay previously caused an extra transition in a synthetic regression environment.",
        issue_type="INCIDENT", severity="HIGH", status="CLOSED",
    ))
    db.add(SupportIssue(
        external_ticket_id="HIST-NOVA-001", client_id=clients["Nova Finance"].id, title="Statement formatting enhancement",
        description="Formatting change requested for a collections statement.", issue_type="CHANGE_REQUEST", severity="LOW", status="CLOSED",
    ))
    db.add(AuditEvent(
        actor="demo-reset", action="DEMO_BASELINE_RESET", object_type="Dataset", object_id=DEMO_VERSION,
        metadata_json={"synthetic": True, "documents": len(DOC_META), "authorities": len(authorities), "ownership_assignments": len(ownership_specs)},
    ))
    db.commit()
    return demo_status(db)


def demo_status(db: Session) -> dict[str, Any]:
    clients = _count(db, Client)
    impls = _count(db, Implementation)
    if db.get_bind().dialect.name != "sqlite":
        docs = _count(db, EvidenceDocument, EvidenceDocument.metadata_json["dataset"].as_string() == DEMO_VERSION)
    else:
        docs = len([d for d in db.scalars(select(EvidenceDocument)).all() if (d.metadata_json or {}).get("dataset") == DEMO_VERSION])
    edges = _count(db, DependencyEdge)
    indexed = _count(db, EvidenceDocument, EvidenceDocument.index_status.in_(["INDEXED", "INDEXED_DEGRADED"]))
    authorities = _count(db, HumanAuthority, HumanAuthority.active.is_(True))
    decision_authorities = _count(db, HumanAuthority, HumanAuthority.active.is_(True), HumanAuthority.can_submit_human_decision.is_(True))
    learning_authorities = _count(db, HumanAuthority, HumanAuthority.active.is_(True), HumanAuthority.can_approve_learning.is_(True))
    recall_authorities = _count(db, HumanAuthority, HumanAuthority.active.is_(True), HumanAuthority.can_authorize_recall.is_(True))
    deployments = _count(db, ImplementationDeployment, ImplementationDeployment.environment == "PRODUCTION", ImplementationDeployment.status == "DEPLOYED")
    ownership = _count(db, ResponsibilityAssignment)
    main_issue = _count(db, SupportIssue, SupportIssue.external_ticket_id == "SUP-PTP-001")
    active_runs = _count(db, AgentRun, AgentRun.status.in_(["QUEUED", "RUNNING", "WAITING_HUMAN"]))
    decisions = _count(db, HumanDecision)
    learnings = _count(db, LearningProposal, LearningProposal.status.in_(["PROPOSED", "APPROVED"]))
    recalls = _count(db, RecallNotice)
    baseline = db.scalar(select(MethodVersion).where(MethodVersion.version == "PTP-EVENT-v1"))
    baseline_approved = bool(baseline and baseline.status == "APPROVED")
    ready = (
        clients >= 3
        and impls >= 3
        and docs >= 10
        and indexed >= docs
        and edges >= 11
        and baseline_approved
        and authorities >= 5
        and decision_authorities >= 2
        and learning_authorities >= 2
        and recall_authorities >= 1
        and deployments >= 3
        and ownership >= 10
        and main_issue == 0
        and active_runs == 0
        and decisions == 0
        and learnings == 0
        and recalls == 0
    )
    return {
        "dataset": DEMO_VERSION,
        "synthetic": True,
        "ready": ready,
        "clients": clients,
        "implementations": impls,
        "documents": docs,
        "indexed_documents": indexed,
        "dependency_edges": edges,
        "baseline_version": baseline.version if baseline else None,
        "baseline_status": baseline.status if baseline else None,
        "active_authorities": authorities,
        "decision_authorities": decision_authorities,
        "learning_authorities": learning_authorities,
        "recall_authorities": recall_authorities,
        "production_deployments": deployments,
        "ownership_assignments": ownership,
        "main_live_issue_count": main_issue,
        "active_analysis_runs": active_runs,
        "human_decisions": decisions,
        "active_learnings": learnings,
        "recalls": recalls,
    }


def demo_readiness(db: Session, *, refresh_runtime: bool = False) -> dict[str, Any]:
    """Return operator-facing, fail-closed demo readiness with explicit blockers."""
    status = demo_status(db)
    settings = get_settings()

    try:
        runtime = get_ollama_runtime().runtime_snapshot(refresh=refresh_runtime)
        qwen_ready = runtime.get("status") == "READY"
        qwen_detail = (
            f"{runtime.get('actual_model') or runtime.get('configured_model')} · inference {runtime.get('inference')}"
            if qwen_ready
            else str(runtime.get("last_error") or "Qwen runtime is not READY")
        )
    except Exception as exc:
        runtime = {"status": "UNAVAILABLE", "last_error": f"{exc.__class__.__name__}: {exc}"}
        qwen_ready = False
        qwen_detail = runtime["last_error"]

    try:
        from app.services.analysis_runs import langgraph_runtime_available
        langgraph_ready, langgraph_reason = langgraph_runtime_available()
    except Exception as exc:
        langgraph_ready, langgraph_reason = False, f"{exc.__class__.__name__}: {exc}"

    checks: list[dict[str, Any]] = []

    def add(key: str, label: str, passed: bool, detail: str, *, warning: bool = False) -> None:
        checks.append({
            "key": key,
            "label": label,
            "status": "WARN" if warning and not passed else ("PASS" if passed else "BLOCKED"),
            "detail": detail,
        })

    add("demo_mode", "Demo reset enabled", settings.demo_mode_enabled, "DEMO_MODE_ENABLED=true" if settings.demo_mode_enabled else "Set DEMO_MODE_ENABLED=true only in the judging environment.")
    add("baseline", "Synthetic governed baseline", status["ready"], f"{status['clients']} clients · {status['implementations']} implementations · {status['documents']} documents · {status['dependency_edges']} A-BOM/evidence edges")
    add("knowledge", "Knowledge indexed", status["documents"] >= 10 and status["indexed_documents"] >= status["documents"], f"{status['indexed_documents']}/{status['documents']} demo documents indexed")
    add("authority", "Human Authority coverage", status["active_authorities"] >= 5 and status["decision_authorities"] >= 2 and status["learning_authorities"] >= 2 and status["recall_authorities"] >= 1, f"{status['active_authorities']} active · decision {status['decision_authorities']} · learning {status['learning_authorities']} · recall {status['recall_authorities']}")
    add("delivery", "Deployment & ownership provenance", status["production_deployments"] >= 3 and status["ownership_assignments"] >= 10, f"{status['production_deployments']} Production deployments · {status['ownership_assignments']} responsibility assignments")
    clean = status["main_live_issue_count"] == 0 and status["active_analysis_runs"] == 0 and status["human_decisions"] == 0 and status["active_learnings"] == 0 and status["recalls"] == 0
    add("clean_case", "Live-case boundary is clean", clean, f"SUP-PTP-001={status['main_live_issue_count']} · active runs={status['active_analysis_runs']} · decisions={status['human_decisions']} · learnings={status['active_learnings']} · recalls={status['recalls']}")
    add("langgraph", "LangGraph runtime", bool(langgraph_ready), "Runtime available" if langgraph_ready else str(langgraph_reason or "LangGraph runtime unavailable"))
    add("qwen", "Qwen execution proof", qwen_ready, qwen_detail)

    degraded_embeddings = _count(db, EvidenceDocument, EvidenceDocument.embedding_degraded.is_(True))
    add("embedding", "Embedding quality", degraded_embeddings == 0, f"{degraded_embeddings} document(s) indexed with degraded/hash fallback", warning=True)
    recall_fixture = _demo_dir() / "RECALL-PTP-V2-001.md"
    add("recall_fixture", "Optional recall evidence staged", recall_fixture.exists(), "backend/demo_data/RECALL-PTP-V2-001.md" if recall_fixture.exists() else "Optional recall evidence file is missing.")

    blockers = [item["key"] for item in checks if item["status"] == "BLOCKED"]
    return {
        "dataset": status,
        "ready": len(blockers) == 0,
        "blocking_checks": blockers,
        "checks": checks,
        "runtime": {
            "qwen_status": runtime.get("status"),
            "configured_model": runtime.get("configured_model"),
            "actual_model": runtime.get("actual_model"),
            "langgraph": "READY" if langgraph_ready else "UNAVAILABLE",
        },
        "live_issue": {
            "ticket": "SUP-PTP-001",
            "client": "Atlas Bank",
            "title": "Network retry replays Promise-to-Pay event",
            "issue_type": "BUG",
            "severity": "HIGH",
        },
    }
