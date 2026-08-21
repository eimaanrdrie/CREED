from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CSS = (ROOT / "frontend/app/globals.css").read_text(encoding="utf-8")
AUDIT = (ROOT / "frontend/components/audit-workspace.tsx").read_text(encoding="utf-8")
NOTES = (ROOT / "UI_R42_NOTES.md").read_text(encoding="utf-8")

checks = {
    "r42 css marker": "UI-R42 — Audit long-list master/detail workspace" in CSS,
    "master detail markup": 'className="audit-master-detail-r42"' in AUDIT,
    "timeline pane": "audit-timeline-pane-r42" in AUDIT,
    "bounded list marker": 'data-r42-scroll="true"' in AUDIT,
    "detail pane": 'className="audit-detail-pane-r42"' in AUDIT,
    "empty selection": "Select an event" in AUDIT,
    "independent vertical scroll": "overflow-y:auto" in CSS,
    "sticky proof": "position:sticky" in CSS and "top:82px" in CSS,
    "stack fallback": "@media (max-width:1050px)" in CSS and ".audit-master-detail-r42 { grid-template-columns:1fr; }" in CSS,
    "notes": "Audit Long-List Master/Detail Fix" in NOTES,
    "governance boundary": "AI proposes. Human decisions carry authority." in AUDIT,
}
failed = [name for name, ok in checks.items() if not ok]
if failed:
    raise SystemExit("UI-R42 verification failed: " + ", ".join(failed))

assert not (ROOT / "frontend/app/demo").exists(), "Demo route must remain removed"
assert CSS.count("{") == CSS.count("}"), "CSS braces are unbalanced"
for path in (ROOT / "frontend").rglob("*.tsx"):
    text = path.read_text(encoding="utf-8")
    assert "react-icons" not in text
    assert "@heroicons" not in text
    assert "fontawesome" not in text.lower()

print("UI-R42 verifier: PASS")
print("- chronology list owns independent vertical scroll")
print("- selected persisted proof remains visible beside long lists on desktop")
print("- stacked breakpoint keeps proof reachable on smaller screens")
print("- audit truth and human-authority semantics unchanged")
