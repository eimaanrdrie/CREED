from __future__ import annotations

from pathlib import Path

import httpx
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker

from app.api.domain import get_domain_db
from app.core.ai_runtime import QwenExecutionRecord
from app.db.base import Base
from app.domain.models import AuditEvent, IssueUnderstanding
from app.main import app
import app.services.issue_understanding as understanding_service


class DynamicFakeRuntime:
    def generate_structured(self, *, prompt, schema_model, node, system_prompt, timeout=None):
        lower = prompt.lower()
        if "duplicate promise-to-pay" in lower or "same ptp event" in lower:
            data = dict(client="Atlas Bank", product="Collections", module="Promise-to-Pay", issue_type="BUG", summary="Duplicate Promise-to-Pay events can produce an incorrect collection state.", suspected_function="PTP event handling", keywords=["duplicate event", "PTP", "state transition"], severity="HIGH", confidence=0.94)
        elif "expiry handling" in lower:
            data = dict(client="Meridian Bank", product="Collections", module="Promise-to-Pay", issue_type="CHANGE_REQUEST", summary="Client requests a change to Promise-to-Pay expiry handling after repayment.", suspected_function="PTP expiry handling", keywords=["PTP expiry", "repayment", "change request"], severity="MEDIUM", confidence=0.9)
        elif "loan application" in lower:
            data = dict(client="Nova Finance", product="Loan Origination", module="Application Intake", issue_type="INCIDENT", summary="Loan application submission is failing during application intake.", suspected_function="application submission", keywords=["loan application", "submission", "intake"], severity="CRITICAL", confidence=0.91)
        elif "interest" in lower:
            data = dict(client=None, product="Loan Management", module="Interest Calculation", issue_type="BUG", summary="Interest calculation is producing an unexpected amount for a repayment case.", suspected_function="interest calculation", keywords=["interest", "repayment", "calculation"], severity="MEDIUM", confidence=0.83)
        else:
            data = dict(client=None, product=None, module=None, issue_type="UNKNOWN", summary="The supplied issue does not contain enough functional context for product or module classification.", suspected_function=None, keywords=["unknown issue"], severity="UNKNOWN", confidence=0.35)
        parsed = schema_model.model_validate(data)
        record = QwenExecutionRecord(
            run_id=f"QWEN-{abs(hash(prompt)) % 100000:05d}", node=node, configured_model="qwen3.5:9b", actual_model="qwen3.5:9b",
            started_at="2026-08-15T09:00:00+00:00", completed_at="2026-08-15T09:00:01+00:00", duration_ms=812.4,
            prompt_eval_count=220, eval_count=68, total_duration_ns=812400000, load_duration_ns=12000000,
            success=True, structured_output_valid=True, error=None,
        )
        return parsed, record, {"model": "qwen3.5:9b"}


class OfflineRuntime:
    def generate_structured(self, **kwargs):
        request = httpx.Request("POST", "http://localhost:11434/api/generate")
        raise httpx.ConnectError("connection refused", request=request)


@pytest.fixture
def context(tmp_path: Path, monkeypatch):
    engine = create_engine(f"sqlite:///{tmp_path / 'm07.db'}", connect_args={"check_same_thread": False})
    Base.metadata.create_all(engine)
    factory = sessionmaker(bind=engine, expire_on_commit=False)

    def override_db():
        with factory() as session:
            yield session

    app.dependency_overrides[get_domain_db] = override_db
    monkeypatch.setattr(understanding_service, "get_ollama_runtime", lambda: DynamicFakeRuntime())
    try:
        yield TestClient(app), factory, monkeypatch
    finally:
        app.dependency_overrides.clear()
        engine.dispose()


def create_issue(client: TestClient, *, bank: str | None, title: str, description: str, issue_type="UNKNOWN", severity="UNKNOWN"):
    client_id = None
    if bank:
        result = client.post("/api/v1/domain/clients", json={"name": bank, "client_type": "BANK"})
        client_id = result.json()["id"]
    result = client.post("/api/v1/issues", json={"client_id": client_id, "title": title, "description": description, "issue_type": issue_type, "severity": severity})
    assert result.status_code == 201, result.text
    return result.json()


def test_real_contract_persists_dynamic_qwen_understanding(context):
    client, factory, _ = context
    issue = create_issue(client, bank="Atlas Bank", title="Duplicate PTP state", description="Atlas Bank reports the same PTP event twice. Duplicate Promise-to-Pay processing changes the collection state.", issue_type="BUG", severity="HIGH")
    response = client.post(f"/api/v1/issues/{issue['id']}/understand")
    assert response.status_code == 201, response.text
    body = response.json()
    assert body["product"] == "Collections"
    assert body["module"] == "Promise-to-Pay"
    assert body["suspected_function"] == "PTP event handling"
    assert body["confidence"] == pytest.approx(0.94)
    assert body["actual_model"] == "qwen3.5:9b"
    assert body["qwen_run_id"].startswith("QWEN-")
    assert body["status"] == "AI_GENERATED"

    with factory() as db:
        saved = db.scalar(select(IssueUnderstanding).where(IssueUnderstanding.issue_id == issue["id"]))
        assert saved is not None
        assert saved.model_output_json["product"] == "Collections"
        audit = db.scalar(select(AuditEvent).where(AuditEvent.action == "ISSUE_UNDERSTANDING_GENERATED"))
        assert audit is not None


def test_latest_understanding_is_retrievable(context):
    client, _, _ = context
    issue = create_issue(client, bank="Meridian Bank", title="Expiry change", description="Meridian Bank wants a change to PTP expiry handling after customer repayment.")
    created = client.post(f"/api/v1/issues/{issue['id']}/understand").json()
    latest = client.get(f"/api/v1/issues/{issue['id']}/understanding")
    assert latest.status_code == 200
    assert latest.json()["id"] == created["id"]
    assert latest.json()["issue_type"] == "CHANGE_REQUEST"


def test_five_inputs_produce_distinct_structured_outputs(context):
    client, _, _ = context
    cases = [
        ("Atlas Bank", "Duplicate PTP", "Duplicate Promise-to-Pay event is received twice and changes state."),
        ("Meridian Bank", "Expiry handling", "Meridian Bank wants a change to PTP expiry handling after customer repayment."),
        ("Nova Finance", "Loan intake", "Nova Finance reports a loan application submission incident in the application intake screen."),
        (None, "Interest discrepancy", "Interest calculation gives an unexpected repayment amount."),
        (None, "Generic problem", "The client says something is wrong but supplied no product or functional details."),
    ]
    outputs = []
    for bank, title, description in cases:
        issue = create_issue(client, bank=bank, title=title, description=description)
        body = client.post(f"/api/v1/issues/{issue['id']}/understand").json()
        outputs.append((body["product"], body["module"], body["issue_type"], tuple(body["keywords"])))
    assert len(set(outputs)) == 5


def test_human_edit_preserves_original_model_output(context):
    client, factory, _ = context
    issue = create_issue(client, bank="Atlas Bank", title="Duplicate PTP", description="Duplicate Promise-to-Pay event is received twice and changes state.")
    created = client.post(f"/api/v1/issues/{issue['id']}/understand").json()
    edited = client.patch(
        f"/api/v1/issues/{issue['id']}/understanding/{created['id']}",
        json={
            "client_name": "Atlas Bank",
            "product": "Juris Collect",
            "module": "Promise-to-Pay",
            "issue_type": "BUG",
            "summary": "Human verified the issue as duplicate Promise-to-Pay event handling within the Collections workflow.",
            "suspected_function": "PTP event handler",
            "keywords": ["PTP", "duplicate event"],
            "severity": "HIGH",
        },
    )
    assert edited.status_code == 200, edited.text
    body = edited.json()
    assert body["status"] == "HUMAN_VERIFIED"
    assert body["product"] == "Juris Collect"
    assert body["human_verified_by"] == "demo-operator"

    with factory() as db:
        saved = db.get(IssueUnderstanding, created["id"])
        assert saved is not None
        assert saved.product == "Juris Collect"
        assert saved.model_output_json["product"] == "Collections"  # immutable original Qwen extraction
        assert db.scalar(select(AuditEvent).where(AuditEvent.action == "ISSUE_UNDERSTANDING_VERIFIED")) is not None


def test_client_mismatch_is_exposed_not_silently_overwritten(context, monkeypatch):
    client, _, _ = context

    class MismatchRuntime(DynamicFakeRuntime):
        def generate_structured(self, *, prompt, schema_model, node, system_prompt, timeout=None):
            parsed, record, raw = super().generate_structured(prompt=prompt, schema_model=schema_model, node=node, system_prompt=system_prompt, timeout=timeout)
            data = parsed.model_dump(); data["client"] = "Different Bank"
            return schema_model.model_validate(data), record, raw

    monkeypatch.setattr(understanding_service, "get_ollama_runtime", lambda: MismatchRuntime())
    issue = create_issue(client, bank="Atlas Bank", title="Duplicate PTP", description="Duplicate Promise-to-Pay event is received twice and changes state.")
    body = client.post(f"/api/v1/issues/{issue['id']}/understand").json()
    assert body["client_name"] == "Different Bank"
    assert "AI_CLIENT_DIFFERS_FROM_HUMAN_SELECTED_CLIENT" in body["warnings"]


def test_qwen_unavailable_fails_closed(context, monkeypatch):
    client, factory, _ = context
    monkeypatch.setattr(understanding_service, "get_ollama_runtime", lambda: OfflineRuntime())
    issue = create_issue(client, bank=None, title="Unavailable runtime", description="A valid issue description that should require actual local inference.")
    response = client.post(f"/api/v1/issues/{issue['id']}/understand")
    assert response.status_code == 503
    assert response.json()["detail"].startswith("QWEN_RUNTIME_UNAVAILABLE")
    with factory() as db:
        assert db.scalar(select(IssueUnderstanding).where(IssueUnderstanding.issue_id == issue["id"])) is None


def test_schema_invalid_first_attempt_gets_one_bounded_retry(context, monkeypatch):
    client, _, _ = context

    class FlakyRuntime(DynamicFakeRuntime):
        calls = 0
        def generate_structured(self, *, prompt, schema_model, node, system_prompt, timeout=None):
            self.calls += 1
            if self.calls == 1:
                # Raise the same validation class a malformed schema response would trigger.
                schema_model.model_validate({"summary": "missing required fields"})
            return super().generate_structured(prompt=prompt, schema_model=schema_model, node=node, system_prompt=system_prompt, timeout=timeout)

    runtime = FlakyRuntime()
    monkeypatch.setattr(understanding_service, "get_ollama_runtime", lambda: runtime)
    issue = create_issue(client, bank="Atlas Bank", title="Duplicate PTP", description="Duplicate Promise-to-Pay event is received twice and changes state.")
    response = client.post(f"/api/v1/issues/{issue['id']}/understand")
    assert response.status_code == 201, response.text
    assert runtime.calls == 2


def test_persistently_invalid_qwen_output_returns_502(context, monkeypatch):
    client, factory, _ = context

    class InvalidRuntime:
        calls = 0
        def generate_structured(self, *, prompt, schema_model, node, system_prompt, timeout=None):
            self.calls += 1
            schema_model.model_validate({"summary": "still missing required fields"})

    runtime = InvalidRuntime()
    monkeypatch.setattr(understanding_service, "get_ollama_runtime", lambda: runtime)
    issue = create_issue(client, bank=None, title="Bad AI output", description="This issue has enough text but the fake runtime will return invalid structured output.")
    response = client.post(f"/api/v1/issues/{issue['id']}/understand")
    assert response.status_code == 502
    assert response.json()["detail"].startswith("AI_OUTPUT_VALIDATION_FAILED")
    assert runtime.calls == 2
    with factory() as db:
        assert db.scalar(select(IssueUnderstanding).where(IssueUnderstanding.issue_id == issue["id"])) is None
