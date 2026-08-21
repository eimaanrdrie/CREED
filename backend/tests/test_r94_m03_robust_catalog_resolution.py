from __future__ import annotations

from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.db.base import Base
from app.domain.models import (
    AgentRun,
    Client,
    DeliveryMethod,
    DependencyEdge,
    Implementation,
    IssueUnderstanding,
    MethodVersion,
    Module,
    Product,
    SupportIssue,
)
from app.services.advanced import resolve_catalog_context, score_blast_radius


def _factory(tmp_path: Path):
    engine = create_engine(f"sqlite:///{tmp_path / 'r94_m03.db'}", connect_args={"check_same_thread": False})
    Base.metadata.create_all(engine)
    return engine, sessionmaker(bind=engine, expire_on_commit=False)


def _seed(tmp_path: Path, *, qwen_module: str | None, client_bound: bool = True, extra_ptp_module: bool = False):
    engine, factory = _factory(tmp_path)
    with factory() as db:
        product = Product(name="Collections", active=True)
        db.add(product)
        db.flush()
        module = Module(product_id=product.id, name="Promise-to-Pay", active=True)
        db.add(module)
        db.flush()
        if extra_ptp_module:
            db.add(Module(product_id=product.id, name="Payment Tracking Platform", active=True))
            db.flush()

        method = DeliveryMethod(module_id=module.id, name="PTP Event Handling")
        db.add(method)
        db.flush()
        version = MethodVersion(method_id=method.id, version="PTP-EVENT-v1", status="APPROVED", summary="Baseline")
        db.add(version)
        db.flush()

        clients = []
        impls = []
        for name in ["Atlas Bank", "Meridian Bank", "Nova Finance"]:
            client = Client(name=name, client_type="BANK")
            db.add(client)
            db.flush()
            impl = Implementation(
                client_id=client.id,
                product_id=product.id,
                module_id=module.id,
                name=f"{name.split()[0]} PTP Implementation",
                release_version="R1",
                status="ACTIVE",
            )
            db.add(impl)
            db.flush()
            db.add(
                DependencyEdge(
                    source_type="Implementation",
                    source_id=impl.id,
                    target_type="MethodVersion",
                    target_id=version.id,
                    relationship="USES_METHOD_VERSION",
                    confidence=1.0,
                )
            )
            clients.append(client)
            impls.append(impl)

        issue = SupportIssue(
            external_ticket_id="SUP-R94-M03",
            client_id=clients[0].id if client_bound else None,
            title="Network retry replays Promise-to-Pay event",
            description="Retry replay may apply another collection-state transition.",
            issue_type="BUG",
            severity="HIGH",
            status="ANALYSING",
        )
        db.add(issue)
        db.flush()
        understanding = IssueUnderstanding(
            issue_id=issue.id,
            qwen_run_id=f"qwen-r94-m03-{qwen_module}-{client_bound}-{extra_ptp_module}",
            input_hash="0" * 64,
            configured_model="qwen-test",
            actual_model="qwen-test",
            product="Collections",
            module=qwen_module,
            issue_type="BUG",
            summary="Promise-to-Pay replay issue",
            suspected_function="event processing",
            keywords_json=["retry", "replay", "idempotency"],
            severity="HIGH",
            confidence=0.9,
            model_output_json={},
        )
        db.add(understanding)
        db.flush()
        run = AgentRun(graph_run_id=f"CREED-R94-M03-{qwen_module}", issue_id=issue.id, status="RUNNING", input_summary=issue.title)
        db.add(run)
        db.commit()
        return engine, factory, {
            "issue_id": issue.id,
            "run_id": run.id,
            "module_id": module.id,
            "version_id": version.id,
            "impl_ids": [item.id for item in impls],
        }


def test_hyphen_insensitive_module_name_routes_registered_implementations(tmp_path: Path):
    engine, factory, ids = _seed(tmp_path, qwen_module="Promise to Pay")
    try:
        with factory() as db:
            context = resolve_catalog_context(db, ids["issue_id"])
            assert context["module"].id == ids["module_id"]
            assert context["module_strategy"] == "CANONICAL_EXACT"
            run = db.get(AgentRun, ids["run_id"])
            result = score_blast_radius(db, run)
            assert result["routing"]["strategy"] == "MODULE_ABOM_UNIQUE_VERSION"
            assert result["routing"]["method_version_id"] == ids["version_id"]
            assert {item["implementation_id"] for item in result["results"]} == set(ids["impl_ids"])
    finally:
        engine.dispose()


def test_ptp_acronym_resolves_only_when_unique(tmp_path: Path):
    engine, factory, ids = _seed(tmp_path, qwen_module="PTP")
    try:
        with factory() as db:
            context = resolve_catalog_context(db, ids["issue_id"])
            assert context["module"].id == ids["module_id"]
            assert context["module_strategy"] == "ACRONYM"
    finally:
        engine.dispose()


def test_longer_qwen_phrase_resolves_catalog_module(tmp_path: Path):
    engine, factory, ids = _seed(tmp_path, qwen_module="Promise-to-Pay event processing")
    try:
        with factory() as db:
            context = resolve_catalog_context(db, ids["issue_id"])
            assert context["module"].id == ids["module_id"]
            assert context["module_strategy"] == "CATALOG_PHRASE"
    finally:
        engine.dispose()


def test_ambiguous_acronym_fails_closed_without_client_anchor(tmp_path: Path):
    engine, factory, ids = _seed(tmp_path, qwen_module="PTP", client_bound=False, extra_ptp_module=True)
    try:
        with factory() as db:
            context = resolve_catalog_context(db, ids["issue_id"])
            assert context["module"] is None
            assert context["module_strategy"] == "AMBIGUOUS_ACRONYM"
            run = db.get(AgentRun, ids["run_id"])
            result = score_blast_radius(db, run)
            assert result["results"] == []
            assert result["routing"]["strategy"] == "UNRESOLVED"
    finally:
        engine.dispose()


def test_reported_client_unique_registered_module_is_safe_fallback(tmp_path: Path):
    engine, factory, ids = _seed(tmp_path, qwen_module="Unknown collections capability", client_bound=True)
    try:
        with factory() as db:
            context = resolve_catalog_context(db, ids["issue_id"])
            assert context["module"].id == ids["module_id"]
            assert context["module_strategy"] == "REPORTED_CLIENT_UNIQUE_MODULE"
            run = db.get(AgentRun, ids["run_id"])
            result = score_blast_radius(db, run)
            assert len(result["results"]) == 3
            assert result["routing"]["strategy"] == "MODULE_ABOM_UNIQUE_VERSION"
    finally:
        engine.dispose()
