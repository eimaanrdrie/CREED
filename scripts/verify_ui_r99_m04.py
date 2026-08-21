from __future__ import annotations

import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

def require(path: str, text: str) -> None:
    data = (ROOT / path).read_text(encoding="utf-8")
    if text not in data:
        raise SystemExit(f"FAIL: {path} missing {text!r}")

require("frontend/components/recalls-workspace.tsx", "Source evidence")
require("frontend/components/recalls-workspace.tsx", "Evidence Repository")
require("frontend/components/recalls-workspace.tsx", "Preview source")
require("frontend/components/recalls-workspace.tsx", "evidence_document_ids: activeEvidenceIds")
require("frontend/components/knowledge-workspace.tsx", "export function KnowledgeSourcePreview")
require("frontend/lib/api.ts", "evidence_document_ids?: string[]")
require("backend/app/api/advanced.py", "evidence_document_ids:list[str]")
require("backend/app/services/advanced.py", "RECALL_EVIDENCE_DOCUMENT_NOT_FOUND")
require("backend/app/services/advanced.py", '"original_filename":d.original_filename')

prev = ROOT / "scripts" / "verify_ui_r99_m03.py"
if prev.exists():
    subprocess.run(["python", str(prev)], cwd=ROOT, check=True)

print("PASS: UI-R99-M04 direct Recall evidence selection + original source preview")
