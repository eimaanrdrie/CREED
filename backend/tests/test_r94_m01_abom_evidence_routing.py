from __future__ import annotations

from pathlib import Path

from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker

from app.db.base import Base
from app.domain.models import (
    AgentRun,
    AnalysisEvidenceHit,
    Client,
    DeliveryMethod,
    DependencyEdge,
    DocumentChunk,
    EvidenceDocument,
    Implementation,
    MethodVersion,
    Module,
    Product,
    SupportIssue,
)
from app.services.advanced import (
    _candidate_evidence,
    _candidate_impl_document_ids,
    resolve_method_versions_from_evidence,
    score_blast_radius,
)


def _seed_ui_style_abom(tmp_path: Path):
    """Seed the exact graph shape created by the R93 Registry > Dependencies UI.

    Important: there are no MethodVersion -> EvidenceDocument or
    Implementation -> EvidenceDocument edges. The only provenance is the
    supporting evidence_document_id persisted on USES_METHOD_VERSION.
    """
    engine = create_engine(f"sqlite:///{tmp_path / 'r94_m01.db'}", connect_args={"check_same_thread": False})
    Base.metadata.create_all(engine)
    factory = sessionmaker(bind=engine, expire_on_commit=False)

    with factory() as db:
        product = Product(name="Collections")
        db.add(product)
        db.flush()
        module = Module(product_id=product.id, name="Promise-to-Pay")
        db.add(module)
        db.flush()
        method = DeliveryMethod(module_id=module.id, name="PTP Event Handling")
        db.add(method)
        db.flush()
        version = MethodVersion(method_id=method.id, version="PTP-EVENT-v1", status="APPROVED", summary="Baseline")
        db.add(version)
        db.flush()

        clients = {}
        implementations = {}
        documents = {}
        config_text = {
            "Atlas Bank": "duplicate_suppression = false\nNetwork retry may replay the same PTP event and apply an extra transition.",
            "Meridian Bank": "duplicate_suppression = false\nRetry replay protection is not enabled for the PTP event handler.",
            "Nova Finance": "duplicate_suppression = true\nidempotency_key_required = true\nReplay protection is enabled.",
        }
        for index, name in enumerate(["Atlas Bank", "Meridian Bank", "Nova Finance"], start=1):
            client = Client(name=name, client_type="BANK" if name != "Nova Finance" else "FINANCIAL_INSTITUTION")
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
            doc = EvidenceDocument(
                source="LOCAL_REPOSITORY",
                title=f"CFG-{name.split()[0].upper()}-PTP-0{index}",
                document_type="CONFIG",
                version="1.0",
                content_hash=f"hash-{index}",
                parse_status="PARSED",
                extracted_text=config_text[name],
                char_count=len(config_text[name]),
                index_status="INDEXED",
            )
            db.add(doc)
            db.flush()
            chunk = DocumentChunk(
                document_id=doc.id,
                chunk_index=0,
                text=config_text[name],
                start_char=0,
                end_char=len(config_text[name]),
                chunk_hash=f"chunk-{index}",
                embedding_vector="[0.0]",
                embedding_provider="TEST",
                embedding_model="TEST",
                embedding_dimensions=1,
            )
            db.add(chunk)
            db.flush()
            db.add(
                DependencyEdge(
                    source_type="Implementation",
                    source_id=impl.id,
                    target_type="MethodVersion",
                    target_id=version.id,
                    relationship="USES_METHOD_VERSION",
                    confidence=1.0,
                    evidence_document_id=doc.id,
                )
            )
            clients[name] = client
            implementations[name] = impl
            documents[name] = (doc, chunk)

        issue = SupportIssue(
            external_ticket_id="SUP-PTP-001",
            client_id=clients["Atlas Bank"].id,
            title="Network retry replays Promise-to-Pay event",
            description=(
                "Atlas Bank reports that a network retry can replay the same Promise-to-Pay event. "
                "The repeated event appears to apply another collection-state transition."
            ),
            issue_type="BUG",
            severity="HIGH",
            status="ANALYSING",
        )
        db.add(issue)
        db.flush()
        run = AgentRun(graph_run_id="CREED-R94-M01", issue_id=issue.id, status="RUNNING", input_summary=issue.title)
        db.add(run)
        db.flush()

        atlas_doc, atlas_chunk = documents["Atlas Bank"]
        db.add(
            AnalysisEvidenceHit(
                agent_run_id=run.id,
                issue_id=issue.id,
                document_id=atlas_doc.id,
                chunk_id=atlas_chunk.id,
                rank=1,
                matched_queries_json=["Promise-to-Pay retry replay"],
                base_score=0.9,
                final_score=0.9,
                semantic_score=0.9,
                keyword_score=0.9,
                metadata_score=0.0,
                citation=atlas_doc.title,
                excerpt=atlas_doc.extracted_text or "",
            )
        )
        db.commit()
        ids = {
            "version": version.id,
            "run": run.id,
            "implementations": {name: impl.id for name, impl in implementations.items()},
            "documents": {name: pair[0].id for name, pair in documents.items()},
        }
    return engine, factory, ids


def test_r93_ui_abom_supporting_evidence_resolves_method_version(tmp_path: Path):
    engine, factory, ids = _seed_ui_style_abom(tmp_path)
    try:
        with factory() as db:
            versions = resolve_method_versions_from_evidence(db, ids["run"])
            assert [version.id for version in versions] == [ids["version"]]
    finally:
        engine.dispose()


def test_r93_ui_abom_supporting_evidence_is_candidate_specific_evidence(tmp_path: Path):
    engine, factory, ids = _seed_ui_style_abom(tmp_path)
    try:
        with factory() as db:
            atlas = db.get(Implementation, ids["implementations"]["Atlas Bank"])
            assert atlas is not None
            doc_ids = _candidate_impl_document_ids(db, atlas.id)
            assert ids["documents"]["Atlas Bank"] in doc_ids
            evidence = _candidate_evidence(db, atlas, ids["version"])
            assert ids["documents"]["Atlas Bank"] in {doc.id for doc in evidence}
    finally:
        engine.dispose()


def test_r93_ui_abom_shape_routes_all_registered_adopters(tmp_path: Path):
    engine, factory, ids = _seed_ui_style_abom(tmp_path)
    try:
        with factory() as db:
            run = db.get(AgentRun, ids["run"])
            assert run is not None
            impact = score_blast_radius(db, run)
            assert len(impact["results"]) == 3
            assert {item["method_version_id"] for item in impact["results"]} == {ids["version"]}
            assert {item["client_name"] for item in impact["results"]} == {"Atlas Bank", "Meridian Bank", "Nova Finance"}
            by_client = {item["client_name"]: item for item in impact["results"]}
            assert by_client["Atlas Bank"]["reported_source"] is True
            assert ids["documents"]["Atlas Bank"] in by_client["Atlas Bank"]["evidence_refs"]
            assert by_client["Nova Finance"]["signals"]["configuration"] == 0.0
    finally:
        engine.dispose()
