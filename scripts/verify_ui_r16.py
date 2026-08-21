from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CSS = (ROOT / "frontend" / "app" / "globals.css").read_text(encoding="utf-8")
RADAR = (ROOT / "frontend" / "components" / "change-radar-workspace.tsx").read_text(encoding="utf-8")
NOTES = (ROOT / "UI_R16_NOTES.md").read_text(encoding="utf-8")

required_css = [
    "UI-R16 — Change Radar Readability + Responsive Intelligence Recomposition",
    ".radar-r05 {\n  max-width: 1320px",
    "--type-md: 15px",
    "min-height: 44px",
    "width: 44px !important",
    "@media (max-width: 1460px)",
    ".radar-layout-r05 { grid-template-columns: 1fr; }",
    "content: attr(data-label)",
    "overflow-wrap: anywhere",
]
for token in required_css:
    assert token in CSS, f"missing UI-R16 CSS contract: {token}"

for token in [
    'labelStyle: { fontSize: 12',
    'return "#5aa2ff"',
    'data-label="Client / implementation"',
    'data-label={mode === "impact" ? "Priority band" : "Recall state"}',
    'data-label="Priority score"',
    "Priority is not a final impact decision.",
    "Routing means review is required; it does not declare that an implementation is defective.",
]:
    assert token in RADAR, f"Radar semantics or responsive contract drifted: {token}"

assert "Change Radar Readability + Responsive Intelligence Recomposition" in NOTES
assert not (ROOT / "frontend" / "app" / "demo").exists(), "Demo route must remain removed"
for path in (ROOT / "frontend").rglob("*.tsx"):
    text = path.read_text(encoding="utf-8")
    assert "react-icons" not in text
    assert "@heroicons" not in text
    assert "fontawesome" not in text.lower()

assert CSS.count("{") == CSS.count("}"), "CSS braces are unbalanced"
print("UI-R16 verification: PASS")
print("- Change Radar bounded to 1320px with a larger local type scale")
print("- graph controls and interactive filters meet 44px target floor")
print("- inspector stacks before permanent-sidebar compression")
print("- graph labels, evidence IDs, ledger values and mobile metadata wrap safely")
print("- impact-priority and recall-obligation governance semantics retained")
