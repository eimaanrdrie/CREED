from fastapi.testclient import TestClient

from app.core.ai_runtime import get_ollama_runtime
from app.main import app

client = TestClient(app)


def test_runtime_endpoint_exposes_real_state_contract(monkeypatch):
    runtime = get_ollama_runtime()
    monkeypatch.setattr(
        runtime,
        "runtime_snapshot",
        lambda refresh=False: {
            "status": "READY",
            "ollama": "CONNECTED",
            "model": "AVAILABLE",
            "inference": "PASSED",
            "configured_model": "qwen3.5:9b",
            "actual_model": "qwen3.5:9b",
            "checked_at": "2026-08-15T00:00:00+00:00",
            "last_error": None,
            "last_inference_duration_ms": 120.5,
            "ollama_base_url": "http://localhost:11434",
            "last_execution": None,
        },
    )
    response = client.get("/api/v1/ai/runtime")
    assert response.status_code == 200
    assert response.json()["status"] == "READY"
    assert response.json()["inference"] == "PASSED"


def test_manual_qwen_endpoint_uses_runtime_result(monkeypatch):
    runtime = get_ollama_runtime()
    monkeypatch.setattr(
        runtime,
        "test_prompt",
        lambda prompt: {
            "run_id": "QWEN-TEST",
            "configured_model": "qwen3.5:9b",
            "actual_model": "qwen3.5:9b",
            "duration_ms": 200.0,
            "prompt_eval_count": 12,
            "eval_count": 8,
            "structured_output_valid": True,
            "output": {"classification": "CREED_TEST", "system": "CREED", "valid": True},
            "completed_at": "2026-08-15T00:00:00+00:00",
        },
    )
    response = client.post("/api/v1/ai/test", json={"prompt": "Classify this as a CREED test"})
    assert response.status_code == 200
    body = response.json()
    assert body["structured_output_valid"] is True
    assert body["output"]["system"] == "CREED"


def test_manual_qwen_endpoint_fails_closed_when_runtime_unavailable(monkeypatch):
    runtime = get_ollama_runtime()

    def unavailable(_: str):
        raise RuntimeError("Configured model is unavailable")

    monkeypatch.setattr(runtime, "test_prompt", unavailable)
    response = client.post("/api/v1/ai/test", json={"prompt": "Classify this as a CREED test"})
    assert response.status_code == 503
    assert "unavailable" in response.json()["detail"].lower()


def test_manual_qwen_endpoint_validates_prompt_length():
    response = client.post("/api/v1/ai/test", json={"prompt": "x"})
    assert response.status_code == 422
