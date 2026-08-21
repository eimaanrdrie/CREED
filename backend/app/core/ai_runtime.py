from __future__ import annotations

import json
import threading
import time
import uuid
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import httpx
from pydantic import BaseModel, Field, ValidationError

from app.core.config import Settings, get_settings


class RuntimeProof(BaseModel):
    status: str
    system: str


class CreedClassification(BaseModel):
    classification: str = Field(description="Short classification for the supplied CREED test input")
    system: str = Field(default="CREED")
    valid: bool


@dataclass
class QwenExecutionRecord:
    run_id: str
    node: str
    configured_model: str
    actual_model: str | None
    started_at: str
    completed_at: str
    duration_ms: float
    prompt_eval_count: int | None
    eval_count: int | None
    total_duration_ns: int | None
    load_duration_ns: int | None
    success: bool
    structured_output_valid: bool
    error: str | None
    queue_duration_ms: float = 0.0
    prompt_eval_duration_ns: int | None = None
    eval_duration_ns: int | None = None


class OllamaRuntime:
    """Thin, explicit Ollama HTTP client used by CREED.

    The runtime never fabricates availability. READY requires reachability,
    configured-model presence, and a successful schema-validated inference.
    """

    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or get_settings()
        self._probe_lock = threading.Lock()
        self._generation_lock = threading.Lock()
        self._last_probe: dict[str, Any] | None = None
        self._last_record: QwenExecutionRecord | None = None

    @staticmethod
    def _utc_now() -> str:
        return datetime.now(timezone.utc).isoformat()

    def _url(self, path: str) -> str:
        return f"{self.settings.ollama_base_url.rstrip('/')}{path}"

    def _write_record(self, record: QwenExecutionRecord) -> None:
        path: Path = self.settings.qwen_log_file
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(asdict(record), ensure_ascii=False) + "\n")
        self._last_record = record

    @staticmethod
    def _http_error_detail(response: httpx.Response) -> str:
        """Return the useful Ollama error body instead of httpx's generic status text."""
        detail: str | None = None
        try:
            body = response.json()
            if isinstance(body, dict):
                value = body.get("error") or body.get("message") or body.get("detail")
                if value is not None:
                    detail = str(value)
                else:
                    detail = json.dumps(body, ensure_ascii=False, separators=(",", ":"))
            elif body is not None:
                detail = str(body)
        except Exception:
            detail = response.text
        compact = " ".join((detail or response.reason_phrase or "Ollama request failed").split())
        return compact[:1200]

    def _request_json(self, method: str, path: str, *, json_body: dict[str, Any] | None = None, timeout: float | None = None) -> dict[str, Any]:
        effective_timeout = timeout if timeout is not None else self.settings.ollama_timeout_seconds
        with httpx.Client(timeout=effective_timeout) as client:
            response = client.request(method, self._url(path), json=json_body)
            if not response.is_success:
                detail = self._http_error_detail(response)
                raise httpx.HTTPStatusError(
                    f"OLLAMA_HTTP_{response.status_code}: {detail}",
                    request=response.request,
                    response=response,
                )
            data = response.json()
            if not isinstance(data, dict):
                raise ValueError("OLLAMA_RESPONSE_NOT_OBJECT")
            return data

    def list_models(self) -> list[str]:
        data = self._request_json("GET", "/api/tags", timeout=self.settings.ollama_health_timeout_seconds)
        models = data.get("models", [])
        names: list[str] = []
        for model in models:
            if isinstance(model, dict):
                name = model.get("name") or model.get("model")
                if isinstance(name, str):
                    names.append(name)
        return names

    def _model_present(self, names: list[str], model: str | None = None) -> bool:
        configured = model or self.settings.ollama_model
        configured_base = configured.split(":", 1)[0]
        for name in names:
            if name == configured:
                return True
            # Ollama may report an implicit :latest tag.
            if ":" not in configured and name.split(":", 1)[0] == configured_base:
                return True
        return False

    def require_model_available(self, model: str) -> None:
        """Fail clearly before generation when the requested task model is not installed."""
        names = self.list_models()
        if not self._model_available(model, names):
            raise ValueError(f"OLLAMA_MODEL_NOT_INSTALLED: {model}")

    def warm_model(self, model: str | None = None) -> dict[str, Any]:
        """Load the live model without creating an inference execution record."""
        configured_model = model or self.settings.live_runtime_model
        timeout = self.settings.ollama_timeout_seconds
        acquired = self._generation_lock.acquire(timeout=timeout)
        if not acquired:
            raise TimeoutError("OLLAMA_GENERATION_QUEUE_TIMEOUT")
        try:
            return self._request_json(
                "POST",
                "/api/generate",
                json_body={
                    "model": configured_model,
                    "prompt": "",
                    "stream": False,
                    "keep_alive": self.settings.ollama_keep_alive,
                    "options": {"num_ctx": self.settings.investigation_context_window},
                },
                timeout=timeout,
            )
        finally:
            self._generation_lock.release()

    @staticmethod
    def _model_available(model_name: str, names: list[str]) -> bool:
        configured_base = model_name.split(":", 1)[0]
        for name in names:
            if name == model_name:
                return True
            if ":" not in model_name and name.split(":", 1)[0] == configured_base:
                return True
        return False

    def generate_structured(
        self,
        *,
        prompt: str,
        schema_model: type[BaseModel],
        node: str,
        system_prompt: str,
        timeout: float | None = None,
        model: str | None = None,
        options: dict[str, Any] | None = None,
        format_schema: dict[str, Any] | None = None,
    ) -> tuple[BaseModel, QwenExecutionRecord, dict[str, Any]]:
        run_id = f"QWEN-{uuid.uuid4().hex[:12].upper()}"
        started_at = self._utc_now()
        started_perf = time.perf_counter()
        raw: dict[str, Any] = {}
        valid = False
        actual_model: str | None = None
        error: str | None = None
        parsed: BaseModel | None = None
        configured_model = model or self.settings.ollama_model
        effective_timeout = timeout if timeout is not None else self.settings.ollama_timeout_seconds
        deadline = started_perf + effective_timeout
        queue_started = time.perf_counter()
        queue_duration_ms = 0.0
        acquired = False

        try:
            acquired = self._generation_lock.acquire(timeout=max(0.0, effective_timeout))
            queue_duration_ms = round((time.perf_counter() - queue_started) * 1000, 2)
            if not acquired:
                raise TimeoutError("OLLAMA_GENERATION_QUEUE_TIMEOUT")
            request_timeout = deadline - time.perf_counter()
            if request_timeout <= 0:
                raise TimeoutError("OLLAMA_GENERATION_DEADLINE_EXCEEDED")
            payload = {
                "model": configured_model,
                "system": system_prompt,
                "prompt": prompt,
                "stream": False,
                "think": False,
                "format": format_schema or schema_model.model_json_schema(),
                "keep_alive": self.settings.ollama_keep_alive,
                "options": {"temperature": 0, **(options or {})},
            }
            raw = self._request_json("POST", "/api/generate", json_body=payload, timeout=request_timeout)
            actual_model_value = raw.get("model")
            actual_model = actual_model_value if isinstance(actual_model_value, str) else None
            response_text = raw.get("response")
            if not isinstance(response_text, str):
                raise ValueError("OLLAMA_RESPONSE_MISSING_TEXT")
            # R94.0.4: detect explicit Ollama completion-budget exhaustion before
            # handing a truncated payload to Pydantic. Older Ollama versions may
            # omit done_reason; malformed JSON is still handled by the Learning
            # retry boundary in create_learning_proposal().
            done_reason = str(raw.get("done_reason") or "").strip().lower()
            if done_reason in {"length", "max_tokens", "token_limit"}:
                raise ValueError(f"OLLAMA_OUTPUT_TRUNCATED: done_reason={done_reason}")
            if raw.get("done") is False:
                raise ValueError("OLLAMA_OUTPUT_INCOMPLETE: done=false")
            parsed = schema_model.model_validate_json(response_text)
            valid = True
        except (httpx.HTTPError, ValueError, ValidationError, json.JSONDecodeError, TimeoutError) as exc:
            error = f"{exc.__class__.__name__}: {exc}"
            raise
        finally:
            if acquired:
                self._generation_lock.release()
            duration_ms = round((time.perf_counter() - started_perf) * 1000, 2)
            record = QwenExecutionRecord(
                run_id=run_id,
                node=node,
                configured_model=configured_model,
                actual_model=actual_model,
                started_at=started_at,
                completed_at=self._utc_now(),
                duration_ms=duration_ms,
                prompt_eval_count=raw.get("prompt_eval_count") if isinstance(raw.get("prompt_eval_count"), int) else None,
                eval_count=raw.get("eval_count") if isinstance(raw.get("eval_count"), int) else None,
                total_duration_ns=raw.get("total_duration") if isinstance(raw.get("total_duration"), int) else None,
                load_duration_ns=raw.get("load_duration") if isinstance(raw.get("load_duration"), int) else None,
                success=valid,
                structured_output_valid=valid,
                error=error,
                queue_duration_ms=queue_duration_ms,
                prompt_eval_duration_ns=raw.get("prompt_eval_duration") if isinstance(raw.get("prompt_eval_duration"), int) else None,
                eval_duration_ns=raw.get("eval_duration") if isinstance(raw.get("eval_duration"), int) else None,
            )
            self._write_record(record)

        assert parsed is not None
        return parsed, record, raw

    def probe(self, *, force: bool = False) -> dict[str, Any]:
        with self._probe_lock:
            if self._last_probe is not None and not force:
                return self._last_probe

            checked_at = self._utc_now()
            configured_model = self.settings.live_runtime_model
            result: dict[str, Any] = {
                "status": "UNAVAILABLE",
                "ollama": "UNAVAILABLE",
                "model": "UNAVAILABLE",
                "inference": "UNAVAILABLE",
                "configured_model": configured_model,
                "actual_model": None,
                "checked_at": checked_at,
                "last_error": None,
                "last_inference_duration_ms": None,
            }
            try:
                names = self.list_models()
                result["ollama"] = "CONNECTED"
                if not self._model_present(names, configured_model):
                    result["model"] = "NOT_INSTALLED"
                    result["last_error"] = f"Configured model '{configured_model}' is not installed in Ollama."
                    self._last_probe = result
                    return result
                result["model"] = "AVAILABLE"

                proof, record, _ = self.generate_structured(
                    prompt='Return exactly the requested structured health object for CREED.',
                    schema_model=RuntimeProof,
                    node="runtime_probe",
                    system_prompt='You are the local CREED runtime health verifier. Return status="ok" and system="CREED".',
                    timeout=self.settings.ollama_timeout_seconds,
                    model=configured_model,
                    options={"num_ctx": self.settings.investigation_context_window, "num_predict": 32},
                )
                if proof.status.lower() != "ok" or proof.system != "CREED":
                    raise ValueError("QWEN_HEALTH_PROOF_MISMATCH")

                result.update(
                    status="READY",
                    inference="PASSED",
                    actual_model=record.actual_model,
                    last_inference_duration_ms=record.duration_ms,
                )
            except (httpx.HTTPError, ValueError, ValidationError, json.JSONDecodeError) as exc:
                result["last_error"] = f"{exc.__class__.__name__}: {exc}"
            self._last_probe = result
            return result

    def test_prompt(self, prompt: str) -> dict[str, Any]:
        # Re-check availability first so the UI never turns a missing runtime into a fake test.
        probe = self.probe(force=True)
        if probe["status"] != "READY":
            raise RuntimeError(probe.get("last_error") or "QWEN_RUNTIME_UNAVAILABLE")

        parsed, record, _ = self.generate_structured(
            prompt=prompt,
            schema_model=CreedClassification,
            node="manual_runtime_test",
            system_prompt=(
                "You are the local Qwen runtime inside CREED. Classify the supplied test input briefly. "
                "Return only schema-conforming data. Set system to CREED and valid to true when you can process the input."
            ),
            model=self.settings.live_runtime_model,
            options={"num_ctx": self.settings.investigation_context_window, "num_predict": 96},
        )
        return {
            "run_id": record.run_id,
            "configured_model": record.configured_model,
            "actual_model": record.actual_model,
            "duration_ms": record.duration_ms,
            "prompt_eval_count": record.prompt_eval_count,
            "eval_count": record.eval_count,
            "structured_output_valid": record.structured_output_valid,
            "output": parsed.model_dump(),
            "completed_at": record.completed_at,
        }

    def recent_execution_records(self, *, limit: int = 12) -> tuple[list[dict[str, Any]], int]:
        """Read persisted Qwen execution provenance without mutating runtime state.

        Malformed historical log lines are ignored rather than breaking the runtime-status
        endpoint. The execution count therefore reflects valid JSON execution records.
        """
        path: Path = self.settings.qwen_log_file
        if not path.exists():
            return ([], 0)

        valid: list[dict[str, Any]] = []
        try:
            with path.open("r", encoding="utf-8") as fh:
                for line in fh:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        item = json.loads(line)
                    except json.JSONDecodeError:
                        continue
                    if isinstance(item, dict) and isinstance(item.get("run_id"), str):
                        valid.append(item)
        except OSError:
            return ([], 0)

        return (list(reversed(valid[-max(1, limit):])), len(valid))

    def runtime_snapshot(self, *, refresh: bool = False) -> dict[str, Any]:
        probe = self.probe(force=refresh)
        last = self._last_record
        recent, execution_count = self.recent_execution_records(limit=12)
        return {
            **probe,
            "ollama_base_url": self.settings.ollama_base_url,
            "last_execution": asdict(last) if last else (recent[0] if recent else None),
            "recent_executions": recent,
            "execution_count": execution_count,
        }


_runtime: OllamaRuntime | None = None


def get_ollama_runtime() -> OllamaRuntime:
    global _runtime
    if _runtime is None:
        _runtime = OllamaRuntime()
    return _runtime
