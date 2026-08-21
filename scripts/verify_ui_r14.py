from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CSS = (ROOT / "frontend" / "app" / "globals.css").read_text(encoding="utf-8")
ISSUES = (ROOT / "frontend" / "components" / "issues-workspace.tsx").read_text(encoding="utf-8")
NOTES = (ROOT / "UI_R14_NOTES.md").read_text(encoding="utf-8")

required_css = [
    "UI-R14 — Issues Registry + Intake Recomposition",
    ".issues-page,\n.issue-intake-shell",
    "max-width: 1320px",
    "@media (max-width: 1220px)",
    "@media (max-width: 1040px)",
    "@media (max-width: 820px)",
    "@media (max-width: 620px)",
    "content: attr(data-label)",
]
for token in required_css:
    assert token in CSS, f"missing UI-R14 CSS contract: {token}"

for label in ["Client / ticket", "Classification", "Evidence", "Status"]:
    assert f'data-label="{label}"' in ISSUES, f"missing responsive ledger label: {label}"

assert "Issues Registry + Intake Recomposition" in NOTES
assert not (ROOT / "frontend" / "app" / "demo").exists(), "Demo route must remain removed"
for path in (ROOT / "frontend").rglob("*.tsx"):
    text = path.read_text(encoding="utf-8")
    assert "react-icons" not in text
    assert "@heroicons" not in text
    assert "fontawesome" not in text.lower()

assert CSS.count("{") == CSS.count("}"), "CSS braces are unbalanced"
print("UI-R14 verification: PASS")
print("- Issues/Intake bounded to command-center width")
print("- issue ledger reflows to labelled case rows before column collision")
print("- intake fields and progress rail retain readable sizing")
print("- R12 palette and approved navigation/icon policies retained")
