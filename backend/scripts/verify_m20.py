from __future__ import annotations
import os, tempfile
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path: sys.path.insert(0,str(ROOT))
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker
from app.db.base import Base
from app.domain.models import AgentRun, Client, SupportIssue
from app.services.demo import reset_demo
from app.services.advanced import discover_evidence, score_blast_radius, dashboard


def main():
    with tempfile.TemporaryDirectory(prefix="creed-m20-") as td:
        db_path=Path(td)/"creed.db";engine=create_engine(f"sqlite:///{db_path}");Base.metadata.create_all(engine);factory=sessionmaker(bind=engine,expire_on_commit=False)
        with factory() as db:
            status=reset_demo(db)
            assert status["ready"] and status["clients"]==3 and status["implementations"]==3 and status["documents"]==9 and status["dependency_edges"]==11
            atlas=db.scalar(select(Client).where(Client.name=="Atlas Bank"));issue=SupportIssue(external_ticket_id="SUP-M20-VERIFY",client_id=atlas.id,title="Network retry replays Promise-to-Pay event",description="A network retry replayed the same Promise-to-Pay event. The repeated event appears to apply another collection-state transition.",issue_type="BUG",severity="HIGH",status="OPEN");db.add(issue);db.flush();run=AgentRun(graph_run_id="CREED-M20-VERIFY",issue_id=issue.id,status="RUNNING",input_summary=issue.title);db.add(run);db.commit()
            ev=discover_evidence(db,run);impact=score_blast_radius(db,run);dash=dashboard(db)
            assert ev["result_count"]>0
            clients={x["client_name"]:x for x in impact["results"]};assert clients["Atlas Bank"]["reported_source"] is True;assert clients["Meridian Bank"]["impact_score"]>clients["Nova Finance"]["impact_score"]
            assert dash["coverage"]["registry"]["percent"]==100.0
            print("PASS: M20 baseline ready — 3 clients / 3 implementations / 9 documents / 11 A-BOM edges")
            print(f"PASS: dynamic issue retrieved {ev['result_count']} ranked evidence items")
            print("PASS: explainable impact ordering differs by actual client evidence")
        engine.dispose()
    if os.getenv("CREED_REQUIRE_LIVE_AI")=="1":
        from app.core.ai_runtime import get_ollama_runtime
        from app.services.analysis_runs import langgraph_runtime_available
        probe=get_ollama_runtime().probe(force=True);assert probe["status"]=="READY",probe
        ok,reason=langgraph_runtime_available();assert ok,reason
        print("PASS: strict live Qwen + LangGraph runtime gate")
    print("PASS: CREED M20 final acceptance verified")

if __name__=="__main__":main()
