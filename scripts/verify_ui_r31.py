from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CSS = (ROOT / "frontend" / "app" / "globals.css").read_text(encoding="utf-8")
SIDEBAR = (ROOT / "frontend" / "components" / "sidebar.tsx").read_text(encoding="utf-8")
NOTES = (ROOT / "UI_R31_NOTES.md").read_text(encoding="utf-8")
DESIGN = (ROOT / "frontend" / "DESIGN.md").read_text(encoding="utf-8")

for token in [
    "UI-R31 — Sidebar System Status Overflow",
    ".system-status-list",
    ".system-status-row",
    "grid-template-columns:20px minmax(0,1fr) minmax(0,auto)",
    "overflow-wrap:anywhere",
    "max-width:112px",
]:
    assert token in CSS, f"missing UI-R31 CSS contract: {token}"

for token in [
    'className="system-status-list"',
    'className={`system-status-row ${stateClass(state)}`}',
    'health?.dependencies.api',
    'health?.dependencies.database',
    'health?.dependencies.qwen',
    'aria-label={`${label}: ${readable}`}',
    '<span>{readable}</span>',
]:
    assert token in SIDEBAR, f"sidebar health contract drifted: {token}"

# R31 intentionally retires the R22 three-column markup, while preserving the
# old CSS harmlessly for compatibility with previous verifier history.
assert 'className="system-signal-strip"' not in SIDEBAR
assert "Knowledge search overflow" in NOTES
assert "Issues metadata/chip overflow" in NOTES
assert "UI-R31 — Width-Safe System Status" in DESIGN
assert not (ROOT / "frontend" / "app" / "demo").exists(), "Demo route must remain removed"

for path in (ROOT / "frontend").rglob("*.tsx"):
    text = path.read_text(encoding="utf-8")
    assert "react-icons" not in text
    assert "@heroicons" not in text
    assert "fontawesome" not in text.lower()

assert CSS.count("{") == CSS.count("}"), "CSS braces are unbalanced"
print("UI-R31 verification: PASS")
print("- sidebar system health reflows vertically instead of competing across three columns")
print("- visible labels remain backend-derived and accessible")
print("- no typography reduction, Demo restoration, or icon-policy drift")
print("- R32 Knowledge search and R33 Issues metadata fixes remain out of scope")
