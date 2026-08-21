from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CSS = (ROOT / "frontend/app/globals.css").read_text(encoding="utf-8")
NOTES = (ROOT / "UI_R43_NOTES.md").read_text(encoding="utf-8")

required = [
    "UI-R43 — Shared panel consistency sweep",
    "--creed-panel-radius: 10px",
    "--creed-panel-border: 1px solid var(--line)",
    ".issue-ledger-r24",
    ".analysis-min-module-r25",
    ".radar-stage-r26",
    ".knowledge-search-stage-r27",
    ".recall-registry-r28",
    ".audit-timeline-pane-r42",
    ".runtime-history-r30",
    "--creed-panel-head-min",
]
missing = [item for item in required if item not in CSS]
assert not missing, f"Missing R43 CSS contract: {missing}"
assert "theme change is not part of R43" in NOTES
print("UI-R43 verifier: PASS")
