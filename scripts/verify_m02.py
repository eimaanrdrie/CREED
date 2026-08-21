#!/usr/bin/env python3
"""CREED M02 acceptance verifier.

Requires the FastAPI backend to be running. It exits non-zero unless the real
Ollama/Qwen runtime is READY and a live structured Qwen test succeeds.
"""

import json
import os
import sys
import urllib.error
import urllib.request

BASE = os.getenv("CREED_API_BASE_URL", "http://127.0.0.1:8000")


def request(path: str, payload=None):
    body = None if payload is None else json.dumps(payload).encode()
    req = urllib.request.Request(
        BASE + path,
        data=body,
        headers={"Content-Type": "application/json"},
        method="GET" if body is None else "POST",
    )
    with urllib.request.urlopen(req, timeout=90) as response:
        return response.status, json.loads(response.read().decode())


def main() -> int:
    print("CREED M02 — real Qwen acceptance")
    try:
        _, runtime = request("/api/v1/ai/runtime?refresh=true")
    except Exception as exc:
        print(f"FAIL: runtime endpoint unavailable: {exc}")
        return 1

    print(json.dumps(runtime, indent=2))
    if runtime.get("status") != "READY":
        print("FAIL: AI engine is not READY. M02 must not be approved.")
        return 2

    try:
        _, result = request(
            "/api/v1/ai/test",
            {"prompt": "Classify this as a CREED test and return structured JSON."},
        )
    except urllib.error.HTTPError as exc:
        print(f"FAIL: Qwen test HTTP {exc.code}: {exc.read().decode()}")
        return 3
    except Exception as exc:
        print(f"FAIL: Qwen test failed: {exc}")
        return 3

    print(json.dumps(result, indent=2))
    if not result.get("structured_output_valid"):
        print("FAIL: Qwen output did not validate against the schema.")
        return 4
    if not result.get("actual_model"):
        print("FAIL: Ollama did not report the actual model.")
        return 5
    if result.get("output", {}).get("system") != "CREED":
        print("FAIL: Qwen output did not satisfy the CREED runtime proof.")
        return 6

    print("PASS: real local Qwen inference verified for M02.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
