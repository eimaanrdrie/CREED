from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TSX = (ROOT / "frontend/components/audit-workspace.tsx").read_text(encoding="utf-8")
CSS = (ROOT / "frontend/app/globals.css").read_text(encoding="utf-8")
NOTES = (ROOT / "UI_R44_NOTES.md").read_text(encoding="utf-8")

required_tsx = [
    'className="audit-head-r44"',
    'className="audit-commandbar-r44"',
    'className="audit-signal-strip-r44"',
    'className="audit-run-context-r44"',
    'className="audit-master-detail-r42"',
    'Persisted only',
    'Inspect run',
]
missing = [x for x in required_tsx if x not in TSX]
assert not missing, f"Missing R44 Audit markup: {missing}"

assert '<section className="audit-glance-r29"' not in TSX, "Old large Audit glance cards still active"
assert '<section className="audit-flow-r29"' not in TSX, "Old duplicate Audit flow still active"
assert 'VisualMetric' not in TSX, "Audit should not use R29 large metric cards after R44"

required_css = [
    "UI-R44 — Audit Workbench Foundation",
    ".audit-commandbar-r44",
    ".audit-signal-strip-r44",
    ".audit-run-context-r44",
    "grid-template-columns:minmax(270px,.72fr) minmax(420px,1.28fr)",
]
missing = [x for x in required_css if x not in CSS]
assert not missing, f"Missing R44 CSS contract: {missing}"

assert "forensic workbench" in NOTES
assert "no backend or audit semantics are changed" in NOTES
print("UI-R44 verifier: PASS")
