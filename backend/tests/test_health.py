from fastapi.testclient import TestClient
from app.main import app
from app.core.ai_runtime import get_ollama_runtime

client = TestClient(app)


def test_liveness():
    response = client.get("/api/v1/health/live")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_health_schema_when_qwen_unavailable(monkeypatch):
    runtime = get_ollama_runtime()
    monkeypatch.setattr(runtime, "runtime_snapshot", lambda refresh=False: {"status": "UNAVAILABLE"})
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["dependencies"]["api"] == "CONNECTED"
    assert data["dependencies"]["qwen"] == "UNAVAILABLE"
    assert data["dependencies"]["knowledge_source"] == "CONNECTED"
    assert data["dependencies"]["database"] in {"NOT_CONFIGURED", "CONNECTED", "UNAVAILABLE"}
