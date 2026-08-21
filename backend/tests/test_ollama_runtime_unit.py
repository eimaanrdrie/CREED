import json

from app.core.ai_runtime import CreedClassification, OllamaRuntime
from app.core.config import Settings


def make_runtime(tmp_path):
    settings = Settings(
        database_url=None,
        ollama_base_url="http://ollama.test",
        ollama_model="qwen3.5:9b",
        ollama_runtime_model="qwen3.5:4b",
        ollama_investigation_model="qwen3.5:4b",
        qwen_log_path=str(tmp_path / "qwen.jsonl"),
    )
    return OllamaRuntime(settings)


def test_probe_requires_model_and_validated_inference(monkeypatch, tmp_path):
    runtime = make_runtime(tmp_path)
    calls = []

    def fake_request(method, path, json_body=None, timeout=None):
        calls.append((method, path, json_body))
        if path == "/api/tags":
            return {"models": [{"name": "qwen3.5:9b"}, {"name": "qwen3.5:4b"}]}
        if path == "/api/generate":
            return {
                "model": "qwen3.5:4b",
                "response": '{"status":"ok","system":"CREED"}',
                "prompt_eval_count": 9,
                "eval_count": 8,
                "total_duration": 250000000,
                "load_duration": 50000000,
            }
        raise AssertionError(path)

    monkeypatch.setattr(runtime, "_request_json", fake_request)
    result = runtime.probe(force=True)

    assert result["status"] == "READY"
    assert result["ollama"] == "CONNECTED"
    assert result["model"] == "AVAILABLE"
    assert result["inference"] == "PASSED"
    generate_payload = next(call[2] for call in calls if call[1] == "/api/generate")
    assert result["configured_model"] == "qwen3.5:4b"
    assert generate_payload["model"] == "qwen3.5:4b"
    assert generate_payload["stream"] is False
    assert generate_payload["think"] is False
    assert generate_payload["keep_alive"] == "30m"
    assert generate_payload["options"]["num_ctx"] == 2048
    assert generate_payload["format"]["type"] == "object"

    log_lines = (tmp_path / "qwen.jsonl").read_text().splitlines()
    assert len(log_lines) == 1
    record = json.loads(log_lines[0])
    assert record["success"] is True
    assert record["actual_model"] == "qwen3.5:4b"
    assert record["prompt_eval_count"] == 9
    assert record["eval_count"] == 8


def test_probe_does_not_run_inference_when_model_missing(monkeypatch, tmp_path):
    runtime = make_runtime(tmp_path)
    monkeypatch.setattr(runtime, "list_models", lambda: ["qwen3.5:0.8b"])
    result = runtime.probe(force=True)
    assert result["status"] == "UNAVAILABLE"
    assert result["ollama"] == "CONNECTED"
    assert result["model"] == "NOT_INSTALLED"
    assert result["inference"] == "UNAVAILABLE"


def test_manual_structured_generation_is_schema_validated(monkeypatch, tmp_path):
    runtime = make_runtime(tmp_path)

    def fake_request(method, path, json_body=None, timeout=None):
        return {
            "model": "qwen3.5:9b",
            "response": '{"classification":"CREED_TEST","system":"CREED","valid":true}',
            "prompt_eval_count": 12,
            "eval_count": 7,
        }

    monkeypatch.setattr(runtime, "_request_json", fake_request)
    parsed, record, _ = runtime.generate_structured(
        prompt="Classify this as a CREED test",
        schema_model=CreedClassification,
        node="unit_test",
        system_prompt="Return structured output",
    )
    assert parsed.system == "CREED"
    assert parsed.valid is True
    assert record.structured_output_valid is True


def test_warm_model_loads_live_model_without_execution_record(monkeypatch, tmp_path):
    runtime = make_runtime(tmp_path)
    calls = []

    def fake_request(method, path, json_body=None, timeout=None):
        calls.append((method, path, json_body))
        return {"model": "qwen3.5:4b", "done": True}

    monkeypatch.setattr(runtime, "_request_json", fake_request)
    result = runtime.warm_model()

    assert result["model"] == "qwen3.5:4b"
    assert calls[0][2] == {
        "model": "qwen3.5:4b",
        "prompt": "",
        "stream": False,
        "keep_alive": "30m",
        "options": {"num_ctx": 2048},
    }
    assert not (tmp_path / "qwen.jsonl").exists()


def test_generation_accepts_constrained_format_schema(monkeypatch, tmp_path):
    runtime = make_runtime(tmp_path)
    supplied_schema = CreedClassification.model_json_schema()
    supplied_schema["properties"]["classification"]["maxLength"] = 20
    captured = {}

    def fake_request(method, path, json_body=None, timeout=None):
        captured.update(json_body)
        return {
            "model": "qwen3.5:4b",
            "response": '{"classification":"CREED_TEST","system":"CREED","valid":true}',
        }

    monkeypatch.setattr(runtime, "_request_json", fake_request)
    runtime.generate_structured(
        prompt="Classify this as a CREED test",
        schema_model=CreedClassification,
        node="unit_test",
        system_prompt="Return structured output",
        model="qwen3.5:4b",
        format_schema=supplied_schema,
    )

    assert captured["format"] == supplied_schema
    assert captured["keep_alive"] == "30m"


def test_runtime_snapshot_exposes_recent_execution_provenance(monkeypatch, tmp_path):
    runtime = make_runtime(tmp_path)
    log_path = tmp_path / "qwen.jsonl"
    log_path.write_text(
        "\n".join(
            [
                json.dumps(
                    {
                        "run_id": "QWEN-OLDER",
                        "node": "runtime_probe",
                        "configured_model": "qwen3.5:9b",
                        "actual_model": "qwen3.5:9b",
                        "started_at": "2026-08-15T00:00:00+00:00",
                        "completed_at": "2026-08-15T00:00:01+00:00",
                        "duration_ms": 100.0,
                        "prompt_eval_count": 5,
                        "eval_count": 4,
                        "total_duration_ns": None,
                        "load_duration_ns": None,
                        "success": True,
                        "structured_output_valid": True,
                        "error": None,
                    }
                ),
                "not-json",
                json.dumps(
                    {
                        "run_id": "QWEN-LATEST",
                        "node": "investigation_agent",
                        "configured_model": "qwen3.5:9b",
                        "actual_model": None,
                        "started_at": "2026-08-15T00:01:00+00:00",
                        "completed_at": "2026-08-15T00:01:02+00:00",
                        "duration_ms": 2000.0,
                        "prompt_eval_count": 25,
                        "eval_count": 0,
                        "total_duration_ns": None,
                        "load_duration_ns": None,
                        "success": False,
                        "structured_output_valid": False,
                        "error": "ConnectError: refused",
                    }
                ),
            ]
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(
        runtime,
        "probe",
        lambda force=False: {
            "status": "UNAVAILABLE",
            "ollama": "UNAVAILABLE",
            "model": "UNAVAILABLE",
            "inference": "UNAVAILABLE",
            "configured_model": "qwen3.5:9b",
            "actual_model": None,
            "checked_at": "2026-08-15T00:02:00+00:00",
            "last_error": "ConnectError: refused",
            "last_inference_duration_ms": None,
        },
    )

    snapshot = runtime.runtime_snapshot(refresh=False)
    assert snapshot["execution_count"] == 2
    assert [item["run_id"] for item in snapshot["recent_executions"]] == ["QWEN-LATEST", "QWEN-OLDER"]
    assert snapshot["recent_executions"][0]["success"] is False
    assert snapshot["last_execution"]["run_id"] == "QWEN-LATEST"
