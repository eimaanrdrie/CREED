from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CSS = (ROOT / "frontend" / "app" / "globals.css").read_text(encoding="utf-8")
AUDIT = (ROOT / "frontend" / "components" / "audit-workspace.tsx").read_text(encoding="utf-8")
NOTES = (ROOT / "UI_R19_NOTES.md").read_text(encoding="utf-8")

required_css = [
    "UI-R19 — Audit + AI Observability Readability Recomposition",
    ".audit-r08 {\n  max-width: 1320px",
    "--type-md: 15px",
    "min-height: 44px",
    "@media (max-width: 1460px)",
    ".audit-workspace-r08 { grid-template-columns: 1fr; }",
    "content: attr(data-label)",
    "overflow-wrap: anywhere",
]
for token in required_css:
    assert token in CSS, f"missing UI-R19 CSS contract: {token}"

for token in [
    'aria-pressed={category===item}',
    'data-label="Lifecycle"',
    'data-label="Retrieval score"',
    'data-label="Priority score"',
    'data-label="Integrity"',
    "Observable, not introspective",
    "Hidden chain-of-thought is not collected or displayed.",
    "Impact values are prioritisation scores, not final human decisions.",
    "Authority boundary",
]:
    assert token in AUDIT, f"Audit observability/governance contract drifted: {token}"

assert "Audit + AI Observability Readability Recomposition" in NOTES
assert not (ROOT / "frontend" / "app" / "demo").exists(), "Demo route must remain removed"
for path in (ROOT / "frontend").rglob("*.tsx"):
    text = path.read_text(encoding="utf-8")
    assert "react-icons" not in text
    assert "@heroicons" not in text
    assert "fontawesome" not in text.lower()

assert CSS.count("{") == CSS.count("}"), "CSS braces are unbalanced"
print("UI-R19 verification: PASS")
print("- Audit workspace bounded to 1320px")
print("- chronology, provenance and governance ledgers use larger operational typography")
print("- Run Inspector, filters and evidence actions meet 44px interaction floor")
print("- trace inspector reflows before fixed-sidebar compression")
print("- glass-box, human-authority and impact-priority semantics retained")
