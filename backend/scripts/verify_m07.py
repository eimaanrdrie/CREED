from __future__ import annotations

import os
import socket
import sqlite3
import subprocess
import sys
import tempfile
import time
from pathlib import Path

import httpx

ROOT = Path(__file__).resolve().parents[1]

CASES = [
    ("Atlas Bank", "Duplicate PTP", "Atlas Bank reports that sending the same Promise-to-Pay event twice sometimes changes the account to an incorrect collection state."),
    ("Meridian Bank", "PTP expiry change", "Meridian Bank wants a change to the PTP expiry handling after customer repayment."),
    ("Nova Finance", "Loan application failure", "Nova Finance reports that a loan application submission fails during application intake."),
    (None, "Interest calculation discrepancy", "Interest calculation produces an unexpected repayment amount in loan management."),
    (None, "Unclassified issue", "A client reports a problem but gives no product, module, or functional detail."),
]


def free_port() -> int:
    sock = socket.socket(); sock.bind(("127.0.0.1", 0)); port = sock.getsockname()[1]; sock.close(); return port


def main() -> int:
    with tempfile.TemporaryDirectory(prefix="creed-m07-") as tmp:
        tmp_path = Path(tmp)
        db_path = tmp_path / "m07.db"
        env = os.environ.copy()
        env.update({
            "DATABASE_URL": f"sqlite:///{db_path}",
            "DOCUMENT_STORAGE_PATH": str(tmp_path / "documents"),
            "EMBEDDING_PROVIDER": "hashing",
            "APP_ENV": "verification",
        })
        subprocess.run(["alembic", "upgrade", "head"], cwd=ROOT, env=env, check=True, stdout=subprocess.DEVNULL)
        with sqlite3.connect(db_path) as conn:
            tables = {row[0] for row in conn.execute("select name from sqlite_master where type='table'")}
            if "issue_understandings" not in tables:
                print("FAIL: M07 migration did not create issue_understandings"); return 1

        port = free_port()
        server = subprocess.Popen(
            [sys.executable, "-m", "uvicorn", "app.main:app", "--host", "127.0.0.1", "--port", str(port)],
            cwd=ROOT, env=env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
        )
        try:
            base = f"http://127.0.0.1:{port}"
            for _ in range(80):
                try:
                    if httpx.get(base + "/api/v1/health/live", timeout=0.4).status_code == 200: break
                except Exception: pass
                time.sleep(0.1)
            else:
                print("FAIL: API did not start"); return 1

            runtime = httpx.get(base + "/api/v1/ai/runtime?refresh=true", timeout=70)
            if runtime.status_code != 200:
                print("FAIL: AI runtime endpoint", runtime.text); return 1
            runtime_body = runtime.json()
            if runtime_body.get("status") != "READY":
                print("FAIL: real local Qwen is not READY; M07 cannot pass live acceptance.")
                print("DETAIL:", runtime_body.get("last_error"))
                return 2

            outputs = []
            with httpx.Client(base_url=base, timeout=100) as client:
                for index, (bank_name, title, description) in enumerate(CASES):
                    client_id = None
                    if bank_name:
                        c = client.post("/api/v1/domain/clients", json={"name": bank_name, "client_type": "BANK"})
                        if c.status_code != 201:
                            print("FAIL client", c.text); return 1
                        client_id = c.json()["id"]
                    issue = client.post("/api/v1/issues", json={
                        "client_id": client_id,
                        "title": title,
                        "description": description,
                        "issue_type": "UNKNOWN",
                        "severity": "UNKNOWN",
                    })
                    if issue.status_code != 201:
                        print("FAIL issue", issue.text); return 1
                    issue_id = issue.json()["id"]
                    result = client.post(f"/api/v1/issues/{issue_id}/understand")
                    if result.status_code != 201:
                        print(f"FAIL Qwen case {index+1}", result.text); return 1
                    body = result.json()
                    if body.get("actual_model") is None or not body.get("qwen_run_id", "").startswith("QWEN-"):
                        print("FAIL: model execution proof missing", body); return 1
                    outputs.append((body.get("product"), body.get("module"), body.get("issue_type"), tuple(body.get("keywords", []))))
                    print(f"PASS case {index+1}: {body.get('product')} / {body.get('module')} / {body.get('issue_type')} / confidence={body.get('confidence')}")

            if len(set(outputs)) < 4:
                print("FAIL: live Qwen outputs were insufficiently dynamic across five different inputs", outputs); return 1

            with sqlite3.connect(db_path) as conn:
                count = conn.execute("select count(*) from issue_understandings").fetchone()[0]
                audits = conn.execute("select count(*) from audit_events where action='ISSUE_UNDERSTANDING_GENERATED'").fetchone()[0]
                agent_runs = conn.execute("select count(*) from agent_runs").fetchone()[0]
            if count != 5 or audits != 5 or agent_runs != 0:
                print("FAIL persisted state", count, audits, agent_runs); return 1

            print("PASS: five real Qwen issue-understanding calls completed with dynamic structured output")
            print("PASS: model execution records and audit provenance persisted")
            print("PASS: agent_runs=0 — LangGraph orchestration remains reserved for M08")
            print("PASS: M07 real-Qwen acceptance verified.")
        finally:
            server.terminate()
            try: server.wait(timeout=3)
            except subprocess.TimeoutExpired: server.kill()

        subprocess.run(["alembic", "downgrade", "base"], cwd=ROOT, env=env, check=True, stdout=subprocess.DEVNULL)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
