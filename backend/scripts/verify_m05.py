from __future__ import annotations

import os
import socket
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
    with tempfile.TemporaryDirectory(prefix="creed-m05-") as tmp:
        tmp_path = Path(tmp)
        env = os.environ.copy()
        env.update({
            "DATABASE_URL": f"sqlite:///{tmp_path / 'm05.db'}",
            "DOCUMENT_STORAGE_PATH": str(tmp_path / "documents"),
            "EMBEDDING_PROVIDER": "hashing",
            "EMBEDDING_DIMENSIONS": "384",
            "APP_ENV": "verification",
        })
        subprocess.run(["alembic", "upgrade", "head"], cwd=ROOT, env=env, check=True, stdout=subprocess.DEVNULL)
        port = free_port()
        server = subprocess.Popen(
            [sys.executable, "-m", "uvicorn", "app.main:app", "--host", "127.0.0.1", "--port", str(port)],
            cwd=ROOT, env=env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
        )
        try:
            base = f"http://127.0.0.1:{port}"
            for _ in range(50):
                try:
                    if httpx.get(base + "/api/v1/health/live", timeout=0.4).status_code == 200: break
                except Exception: pass
                time.sleep(0.1)
            else:
                print("FAIL: API did not start"); return 1

            docs = [
                ("FSD-COL-104.txt", "FSD-COL-104", "Promise-to-Pay duplicate events require idempotent event handling. Replayed PTP events must not transition collection state twice."),
                ("ONBOARDING.txt", "Customer Onboarding", "Customer onboarding captures identity documents, residential address and KYC verification before account activation."),
                ("TC-COL-217.txt", "TC-COL-217", "Test duplicate Promise-to-Pay event replay. The second identical event must return the existing state without another transition."),
            ]
            with httpx.Client(base_url=base, timeout=15) as client:
                for filename, title, content in docs:
                    response = client.post("/api/v1/documents", data={"title": title, "source": "LOCAL_DEMO"}, files={"file": (filename, content.encode(), "text/plain")})
                    if response.status_code != 201:
                        print("FAIL upload", title, response.text); return 1
                    item = response.json()
                    if item["chunk_count"] < 1 or item["index_status"] != "INDEXED_DEGRADED":
                        print("FAIL index", item); return 1

                result = client.post("/api/v1/retrieval/search", json={"query": "duplicate Promise-to-Pay event replay", "top_k": 5}).json()
                if not result["results"]:
                    print("FAIL: no retrieval results"); return 1
                if result["results"][0]["document_title"] not in {"FSD-COL-104", "TC-COL-217"}:
                    print("FAIL: unrelated document ranked first", result["results"][0]); return 1
                filtered = client.post("/api/v1/retrieval/search", json={"query": "duplicate event", "document_type": "TXT", "top_k": 5}).json()
                if not filtered["results"]:
                    print("FAIL: metadata-filtered search returned nothing"); return 1
                status = client.get("/api/v1/retrieval/status").json()

            print(f"PASS: {status['indexed_documents']} documents indexed into {status['chunks']} chunks")
            print(f"PASS: top result = {result['results'][0]['document_title']} score={result['results'][0]['score']}")
            print(f"PASS: citation = {result['results'][0]['citation']}")
            print(f"PASS: embedding provider = {result['embedding']['provider']} dimensions={result['embedding']['dimensions']} degraded={result['embedding']['degraded']}")
            print("PASS: M05 chunking, local vectors, hybrid ranking, metadata filters and citations verified.")
        finally:
            server.terminate()
            try: server.wait(timeout=3)
            except subprocess.TimeoutExpired: server.kill()
        subprocess.run(["alembic", "downgrade", "base"], cwd=ROOT, env=env, check=True, stdout=subprocess.DEVNULL)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
