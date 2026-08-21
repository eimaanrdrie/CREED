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


def free_port() -> int:
    sock = socket.socket(); sock.bind(("127.0.0.1", 0)); port = sock.getsockname()[1]; sock.close(); return port


def main() -> int:
    with tempfile.TemporaryDirectory(prefix="creed-m06-") as tmp:
        tmp_path = Path(tmp)
        db_path = tmp_path / "m06.db"
        env = os.environ.copy()
        env.update({
            "DATABASE_URL": f"sqlite:///{db_path}",
            "DOCUMENT_STORAGE_PATH": str(tmp_path / "documents"),
            "EMBEDDING_PROVIDER": "hashing",
            "EMBEDDING_DIMENSIONS": "384",
            "APP_ENV": "verification",
        })
        subprocess.run(["alembic", "upgrade", "head"], cwd=ROOT, env=env, check=True, stdout=subprocess.DEVNULL)

        with sqlite3.connect(db_path) as conn:
            tables = {row[0] for row in conn.execute("select name from sqlite_master where type='table'")}
            if "issue_evidence_links" not in tables:
                print("FAIL: M06 migration did not create issue_evidence_links"); return 1

        port = free_port()
        server = subprocess.Popen(
            [sys.executable, "-m", "uvicorn", "app.main:app", "--host", "127.0.0.1", "--port", str(port)],
            cwd=ROOT, env=env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
        )
        try:
            base = f"http://127.0.0.1:{port}"
            for _ in range(60):
                try:
                    if httpx.get(base + "/api/v1/health/live", timeout=0.4).status_code == 200: break
                except Exception: pass
                time.sleep(0.1)
            else:
                print("FAIL: API did not start"); return 1

            with httpx.Client(base_url=base, timeout=20) as client:
                bank_resp = client.post("/api/v1/domain/clients", json={"name": "Atlas Bank", "client_type": "BANK"})
                if bank_resp.status_code != 201:
                    print("FAIL client", bank_resp.text); return 1
                bank = bank_resp.json()

                issue_resp = client.post("/api/v1/issues", json={
                    "external_ticket_id": "SUP-2317",
                    "client_id": bank["id"],
                    "title": "Duplicate Promise-to-Pay event changes collection state",
                    "description": "Atlas Bank reports duplicate PTP events can cause the collection state to transition incorrectly.",
                    "issue_type": "BUG",
                    "severity": "HIGH",
                })
                if issue_resp.status_code != 201:
                    print("FAIL issue", issue_resp.text); return 1
                issue = issue_resp.json()
                if issue["status"] != "OPEN" or issue["attachment_count"] != 0:
                    print("FAIL issue state", issue); return 1

                evidence_resp = client.post(
                    "/api/v1/documents",
                    data={"source": "ISSUE_ATTACHMENT", "issue_id": issue["id"], "title": "SUP-2317 production trace"},
                    files={"file": ("SUP-2317-trace.txt", b"Duplicate PTP event observed twice in the production trace.", "text/plain")},
                )
                if evidence_resp.status_code != 201:
                    print("FAIL evidence", evidence_resp.text); return 1

                detail = client.get(f"/api/v1/issues/{issue['id']}")
                if detail.status_code != 200:
                    print("FAIL detail", detail.text); return 1
                capsule = detail.json()
                if capsule["attachment_count"] != 1 or capsule["attachments"][0]["document_id"] != evidence_resp.json()["id"]:
                    print("FAIL evidence link", capsule); return 1

                listed = client.get("/api/v1/issues").json()
                if len(listed) != 1 or listed[0]["external_ticket_id"] != "SUP-2317":
                    print("FAIL issue registry", listed); return 1

            with sqlite3.connect(db_path) as conn:
                issue_count = conn.execute("select count(*) from support_issues").fetchone()[0]
                link_count = conn.execute("select count(*) from issue_evidence_links").fetchone()[0]
                agent_runs = conn.execute("select count(*) from agent_runs").fetchone()[0]
                audit_count = conn.execute("select count(*) from audit_events where action in ('ISSUE_CREATED','ISSUE_EVIDENCE_LINKED')").fetchone()[0]
            if (issue_count, link_count, agent_runs) != (1, 1, 0):
                print("FAIL persisted state", issue_count, link_count, agent_runs); return 1
            if audit_count != 2:
                print("FAIL audit events", audit_count); return 1

            print("PASS: Issue Capsule persisted through live HTTP API")
            print("PASS: support ticket SUP-2317 linked to Atlas Bank")
            print("PASS: 1 uploaded evidence document linked through issue_evidence_links")
            print("PASS: issue remained OPEN and agent_runs=0 — no fabricated AI execution")
            print("PASS: ISSUE_CREATED and ISSUE_EVIDENCE_LINKED audit events persisted")
            print("PASS: M06 issue intake, evidence linking and analysis-shell boundary verified.")
        finally:
            server.terminate()
            try: server.wait(timeout=3)
            except subprocess.TimeoutExpired: server.kill()

        subprocess.run(["alembic", "downgrade", "base"], cwd=ROOT, env=env, check=True, stdout=subprocess.DEVNULL)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
