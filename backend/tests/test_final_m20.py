from pathlib import Path
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient
from app.db.base import Base
from app.domain.models import AgentRun, Client, SupportIssue, MethodVersion
from app.services.demo import reset_demo
from app.services.advanced import discover_evidence, score_blast_radius, dashboard, method_abom, canonical_hash
from app.api.domain import get_domain_db
from app.main import app


def context(tmp_path:Path):
    engine=create_engine(f"sqlite:///{tmp_path/'m20.db'}",connect_args={"check_same_thread":False});Base.metadata.create_all(engine);factory=sessionmaker(bind=engine,expire_on_commit=False);return engine,factory

def test_demo_reset_is_repeatable_and_complete(tmp_path):
    engine,factory=context(tmp_path)
    with factory() as db:
        first=reset_demo(db);second=reset_demo(db)
        assert first["ready"] and second["ready"]
        assert second["clients"]==3 and second["implementations"]==3 and second["documents"]==10 and second["dependency_edges"]==11
        v=db.scalar(select(MethodVersion).where(MethodVersion.version=="PTP-EVENT-v1"));a=method_abom(db,v.id)
        assert a["clients"]==3 and len(a["implementations"])==3 and len(a["documents"])==5
    engine.dispose()

def test_dynamic_issue_retrieval_and_impact_are_not_static(tmp_path):
    engine,factory=context(tmp_path)
    with factory() as db:
        reset_demo(db);atlas=db.scalar(select(Client).where(Client.name=="Atlas Bank"))
        issue=SupportIssue(external_ticket_id="SUP-DYNAMIC-1",client_id=atlas.id,title="Network retry duplicates PTP event",description="A network retry replayed the same Promise-to-Pay event and appears to apply another collection state transition.",issue_type="BUG",severity="HIGH",status="OPEN");db.add(issue);db.flush()
        run=AgentRun(graph_run_id="CREED-M20-DYNAMIC",issue_id=issue.id,status="RUNNING",input_summary=issue.title);db.add(run);db.commit()
        evidence=discover_evidence(db,run);impact=score_blast_radius(db,run)
        assert evidence["result_count"]>0 and any("PTP" in x["citation"] for x in evidence["results"])
        by_client={x["client_name"]:x for x in impact["results"]}
        assert by_client["Atlas Bank"]["reported_source"] is True
        assert by_client["Meridian Bank"]["impact_score"] > by_client["Nova Finance"]["impact_score"]
        assert by_client["Nova Finance"]["impact_band"]=="MEDIUM"
    engine.dispose()

def test_issue_api_is_idempotent_for_same_ticket_and_content(tmp_path):
    engine,factory=context(tmp_path)
    with factory() as db: reset_demo(db);atlas=db.scalar(select(Client).where(Client.name=="Atlas Bank"));atlas_id=atlas.id
    def override():
        with factory() as db: yield db
    app.dependency_overrides[get_domain_db]=override
    try:
        client=TestClient(app);payload={"external_ticket_id":"SUP-IDEMP-1","client_id":atlas_id,"title":"Duplicate PTP event","description":"Duplicate Promise-to-Pay event repeated after a retry.","issue_type":"BUG","severity":"HIGH"}
        first=client.post("/api/v1/issues",json=payload);second=client.post("/api/v1/issues",json=payload)
        assert first.status_code==201 and second.status_code==200 and first.json()["id"]==second.json()["id"]
        conflict=client.post("/api/v1/issues",json={**payload,"description":"Materially different content for the same ticket."})
        assert conflict.status_code==409
    finally: app.dependency_overrides.clear();engine.dispose()

def test_dashboard_uses_persisted_denominators(tmp_path):
    engine,factory=context(tmp_path)
    with factory() as db:
        reset_demo(db);data=dashboard(db)
        assert data["coverage"]["registry"]["numerator"]==3
        assert data["coverage"]["registry"]["denominator"]==3
        assert data["coverage"]["registry"]["percent"]==100.0
    engine.dispose()

def test_canonical_integrity_hash_detects_payload_change():
    payload={"version":"v2","evidence":["A","B"],"human":"Reviewer"}
    assert canonical_hash(payload)==canonical_hash(dict(payload))
    assert canonical_hash(payload)!=canonical_hash({**payload,"version":"v3"})
