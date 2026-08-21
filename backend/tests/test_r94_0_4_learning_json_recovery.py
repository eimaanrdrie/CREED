from __future__ import annotations

import json
import re
from pathlib import Path

import httpx
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.ai_runtime import OllamaRuntime, QwenExecutionRecord
from app.core.config import Settings, get_settings
from app.db.base import Base
from app.domain.models import (
    AgentRun,
    AnalysisImpactAssessment,
    Client,
    DeliveryMethod,
    EvidenceDocument,
    Finding,
    HumanDecision,
    Implementation,
    Investigation,
    MethodVersion,
    Module,
    Product,
    SupportIssue,
)
from app.services.advanced import LearningOutput, create_learning_proposal
import app.services.advanced as advanced_service


def _factory(tmp_path: Path):
    engine = create_engine(f"sqlite:///{tmp_path / 'r94_0_4.db'}", connect_args={"check_same_thread": False})
    Base.metadata.create_all(engine)
    return engine, sessionmaker(bind=engine, expire_on_commit=False)


def _seed(factory, *, evidence_chars: int = 6000):
    with factory() as db:
        product = Product(name="Collections", description="Collections", active=True)
        db.add(product); db.flush()
        module = Module(product_id=product.id, name="Promise-to-Pay", description="PTP", active=True)
        db.add(module); db.flush()
        method = DeliveryMethod(module_id=module.id, name="PTP Event Handling", description="PTP")
        db.add(method); db.flush()
        version = MethodVersion(method_id=method.id, version="PTP-EVENT-v1", status="APPROVED", summary="Baseline")
        db.add(version); db.flush()
        client = Client(name="Atlas Bank", client_type="BANK")
        db.add(client); db.flush()
        impl = Implementation(client_id=client.id, product_id=product.id, module_id=module.id, name="Atlas PTP Implementation", release_version="R1", status="ACTIVE")
        db.add(impl); db.flush()
        issue = SupportIssue(client_id=client.id, external_ticket_id="SUP-R9404", title="Retry replay", description="Retry replay", issue_type="BUG", severity="HIGH", status="OPEN")
        db.add(issue); db.flush()
        run = AgentRun(graph_run_id="CREED-R94-0-4", issue_id=issue.id, status="COMPLETED")
        db.add(run); db.flush()
        inv = Investigation(issue_id=issue.id, agent_run_id=run.id, implementation_id=impl.id, status="COMPLETED", risk_score=.8)
        db.add(inv); db.flush()
        doc = EvidenceDocument(
            source="LOCAL_REPOSITORY", title="CFG-ATLAS-PTP-01", document_type="CONFIG", version="1.0",
            content_hash="r9404-doc", extracted_text="X" * evidence_chars, char_count=evidence_chars,
            parse_status="PARSED", index_status="INDEXED", metadata_json={}, chunk_count=1, embedding_degraded=False,
        )
        db.add(doc); db.flush()
        db.add(Finding(investigation_id=inv.id, finding_type="POTENTIALLY_AFFECTED", statement="Replay evidence", confidence=.9, evidence_refs=[doc.id]))
        db.add(HumanDecision(investigation_id=inv.id, decision="AFFECTED", reviewer="aisha.rahman@creed.example", reason="Evidence supports impact", metadata_json={"graph_run_id": run.graph_run_id}))
        db.add(AnalysisImpactAssessment(agent_run_id=run.id, issue_id=issue.id, implementation_id=impl.id, method_version_id=version.id, impact_score=.8, impact_band="HIGH", reported_source=True, signals_json={}, weights_json={}, explanation_json=[], evidence_refs_json=[doc.id]))
        db.commit()
        return run.id, doc.id


def _record(node: str) -> QwenExecutionRecord:
    return QwenExecutionRecord(
        run_id="QWEN-R9404", node=node, configured_model="qwen3.5:4b", actual_model="qwen3.5:4b",
        started_at="2026-08-21T00:00:00+00:00", completed_at="2026-08-21T00:00:01+00:00",
        duration_ms=900.0, prompt_eval_count=500, eval_count=200, total_duration_ns=900000000,
        load_duration_ns=10000000, success=True, structured_output_valid=True, error=None,
    )


class RetryRuntime:
    def __init__(self, evidence_id: str):
        self.evidence_id = evidence_id
        self.calls = []

    def require_model_available(self, model: str):
        assert model == "qwen3.5:4b"

    def generate_structured(self, *, prompt, schema_model, node, system_prompt, timeout=None, **kwargs):
        self.calls.append({"prompt": prompt, "options": kwargs.get("options"), "model": kwargs.get("model")})
        if len(self.calls) == 1:
            # Reproduce the user's EOF/mid-string failure through Pydantic's JSON validator.
            schema_model.model_validate_json('{"title":"Idempotency","reusable_learning":"unterminated')
        parsed = schema_model.model_validate({
            "title": "Idempotent Promise-to-Pay handling",
            "reusable_learning": "Check a stable idempotency key before mutating Promise-to-Pay state.",
            "applicability": "Promise-to-Pay handlers that can receive network retries.",
            "guardrails": ["Do not reuse a key across distinct business updates."],
            "validation_steps": ["Replay the same event key and confirm one state transition."],
            "evidence_ids": [self.evidence_id],
        })
        return parsed, _record(node), {"model": "qwen3.5:4b", "done": True, "done_reason": "stop"}


class AlwaysTruncatedRuntime:
    def __init__(self):
        self.calls = 0

    def require_model_available(self, model: str):
        pass

    def generate_structured(self, **kwargs):
        self.calls += 1
        raise ValueError("OLLAMA_OUTPUT_TRUNCATED: done_reason=length")


def test_learning_budget_defaults_are_explicit():
    settings = Settings(database_url=None)
    assert settings.learning_context_window == 8192
    assert settings.learning_num_predict == 900
    assert settings.learning_excerpt_chars == 1400
    assert settings.learning_generation_attempts == 3


def test_runtime_reports_explicit_ollama_length_stop(monkeypatch, tmp_path: Path):
    runtime = OllamaRuntime(Settings(database_url=None, ollama_base_url="http://ollama.test", qwen_log_path=str(tmp_path / "qwen.jsonl")))

    class FakeClient:
        def __init__(self, *args, **kwargs): pass
        def __enter__(self): return self
        def __exit__(self, exc_type, exc, tb): return False
        def request(self, method, url, json=None):
            req = httpx.Request(method, url)
            return httpx.Response(200, request=req, json={
                "model": "qwen3.5:4b", "response": '{"title":"cut off', "done": True, "done_reason": "length"
            })

    monkeypatch.setattr(httpx, "Client", FakeClient)
    with pytest.raises(ValueError, match="OLLAMA_OUTPUT_TRUNCATED: done_reason=length"):
        runtime.generate_structured(
            prompt="Return JSON", schema_model=LearningOutput, node="learning_agent",
            system_prompt="Return JSON", model="qwen3.5:4b",
            options={"num_ctx": 8192, "num_predict": 900},
        )
    record = json.loads((tmp_path / "qwen.jsonl").read_text().strip())
    assert "OLLAMA_OUTPUT_TRUNCATED" in record["error"]


def test_learning_retries_malformed_json_with_compact_budget_and_succeeds(tmp_path: Path, monkeypatch):
    engine, factory = _factory(tmp_path)
    try:
        run_id, evidence_id = _seed(factory)
        runtime = RetryRuntime(evidence_id)
        monkeypatch.setattr(advanced_service, "get_ollama_runtime", lambda: runtime)
        settings = get_settings()
        monkeypatch.setattr(settings, "learning_context_window", 8192)
        monkeypatch.setattr(settings, "learning_num_predict", 900)
        monkeypatch.setattr(settings, "learning_excerpt_chars", 1400)
        monkeypatch.setattr(settings, "learning_generation_attempts", 3)

        with factory() as db:
            run = db.get(AgentRun, run_id)
            result = create_learning_proposal(
                db, run, new_version="PTP-EVENT-v2",
                corrected_method="Require an idempotency-key check before every Promise-to-Pay state mutation.",
                author="aisha.rahman@creed.example",
            )
            assert result["status"] == "PROPOSED"
            assert result["proposed_method_version"]["version"] == "PTP-EVENT-v2"

        assert len(runtime.calls) == 2
        assert runtime.calls[0]["options"] == {"num_ctx": 8192, "num_predict": 900}
        assert runtime.calls[1]["options"] == {"num_ctx": 8192, "num_predict": 900}
        assert "RETRY INSTRUCTION" in runtime.calls[1]["prompt"]
        match = re.search(r"<UNTRUSTED_DATA>\n(X+)\n</UNTRUSTED_DATA>", runtime.calls[0]["prompt"])
        assert match is not None
        assert len(match.group(1)) == 1400
    finally:
        engine.dispose()


def test_learning_truncation_exhaustion_has_clear_error(tmp_path: Path, monkeypatch):
    engine, factory = _factory(tmp_path)
    try:
        run_id, _ = _seed(factory, evidence_chars=2000)
        runtime = AlwaysTruncatedRuntime()
        monkeypatch.setattr(advanced_service, "get_ollama_runtime", lambda: runtime)
        settings = get_settings()
        monkeypatch.setattr(settings, "learning_generation_attempts", 3)
        with factory() as db:
            run = db.get(AgentRun, run_id)
            with pytest.raises(ValueError, match="LEARNING_OUTPUT_TRUNCATED_AFTER_RETRY"):
                create_learning_proposal(
                    db, run, new_version="PTP-EVENT-v2",
                    corrected_method="Require idempotency before state mutation.",
                    author="aisha.rahman@creed.example",
                )
        assert runtime.calls == 3
    finally:
        engine.dispose()
