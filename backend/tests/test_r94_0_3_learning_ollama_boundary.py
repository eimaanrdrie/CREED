from __future__ import annotations

import json

import httpx
import pytest

from app.core.ai_runtime import CreedClassification, OllamaRuntime
from app.core.config import Settings
from app.services.advanced import _learning_format_schema


def _runtime(tmp_path):
    return OllamaRuntime(
        Settings(
            database_url=None,
            ollama_base_url="http://ollama.test",
            ollama_model="qwen3.5:9b",
            ollama_runtime_model="qwen3.5:4b",
            ollama_investigation_model="qwen3.5:4b",
            ollama_learning_model="qwen3.5:4b",
            qwen_log_path=str(tmp_path / "qwen.jsonl"),
        )
    )


def test_learning_defaults_to_dedicated_4b_model_and_simple_schema():
    settings = Settings(database_url=None)
    assert settings.ollama_learning_model == "qwen3.5:4b"

    schema = _learning_format_schema(["DOC-A", "DOC-B"])
    assert schema["type"] == "object"
    assert "$defs" not in schema
    assert "title" in schema["properties"]
    assert schema["properties"]["evidence_ids"]["items"]["enum"] == ["DOC-A", "DOC-B"]

    encoded = json.dumps(schema)
    # Keep the Ollama format contract intentionally small. Pydantic still applies
    # the strict min/max validation after the model returns JSON.
    assert "maxLength" not in encoded
    assert "minLength" not in encoded
    assert "maxItems" not in encoded


def test_learning_model_preflight_fails_with_clear_model_name(monkeypatch, tmp_path):
    runtime = _runtime(tmp_path)
    monkeypatch.setattr(runtime, "list_models", lambda: ["qwen3.5:9b"])

    with pytest.raises(ValueError, match=r"OLLAMA_MODEL_NOT_INSTALLED: qwen3\.5:4b"):
        runtime.require_model_available("qwen3.5:4b")


def test_ollama_400_preserves_real_response_body_and_execution_log(monkeypatch, tmp_path):
    runtime = _runtime(tmp_path)

    class FakeClient:
        def __init__(self, *args, **kwargs):
            pass

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

        def request(self, method, url, json=None):
            request = httpx.Request(method, url)
            return httpx.Response(
                400,
                request=request,
                json={"error": "invalid format schema for this model"},
            )

    monkeypatch.setattr(httpx, "Client", FakeClient)

    with pytest.raises(httpx.HTTPStatusError, match="OLLAMA_HTTP_400: invalid format schema for this model"):
        runtime.generate_structured(
            prompt="Return a structured CREED object",
            schema_model=CreedClassification,
            node="learning_agent",
            system_prompt="Return structured output",
            model="qwen3.5:4b",
            format_schema={
                "type": "object",
                "properties": {
                    "classification": {"type": "string"},
                    "system": {"type": "string"},
                    "valid": {"type": "boolean"},
                },
                "required": ["classification", "system", "valid"],
            },
        )

    record = json.loads((tmp_path / "qwen.jsonl").read_text().strip())
    assert record["success"] is False
    assert "OLLAMA_HTTP_400: invalid format schema for this model" in record["error"]
    assert record["configured_model"] == "qwen3.5:4b"
