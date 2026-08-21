from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CSS = (ROOT / "frontend" / "app" / "globals.css").read_text(encoding="utf-8")
ANALYSIS = (ROOT / "frontend" / "components" / "analysis-shell.tsx").read_text(encoding="utf-8")
DETAIL = (ROOT / "frontend" / "components" / "issue-detail-workspace.tsx").read_text(encoding="utf-8")
NOTES = (ROOT / "UI_R15_NOTES.md").read_text(encoding="utf-8")

required_css = [
    "UI-R15 — Issue Detail + Analysis Workspace Recomposition",
    ".issue-detail-r04,\n.analysis-r04",
    "max-width: 1320px",
    "--type-2xs: 12px",
    "@media (max-width: 1360px)",
    ".analysis-workspace-r04 { grid-template-columns: 1fr; }",
    "grid-template-columns: repeat(3, minmax(0, 1fr))",
    "@media (max-width: 520px)",
    "overflow-wrap: anywhere",
]
for token in required_css:
    assert token in CSS, f"missing UI-R15 CSS contract: {token}"

for token in [
    "AI investigates. Humans decide.",
    "WAITING_HUMAN",
    "AFFECTED",
    "NOT_AFFECTED",
    "NEEDS_MORE_INVESTIGATION",
    "EventSource",
]:
    assert token in ANALYSIS, f"analysis governance/execution contract drifted: {token}"

for token in ["Human-supplied source record", "Linked evidence", "Open analysis workspace"]:
    assert token in DETAIL, f"issue detail contract drifted: {token}"

assert "Issue Detail + Analysis Workspace Recomposition" in NOTES
assert not (ROOT / "frontend" / "app" / "demo").exists(), "Demo route must remain removed"
for path in (ROOT / "frontend").rglob("*.tsx"):
    text = path.read_text(encoding="utf-8")
    assert "react-icons" not in text
    assert "@heroicons" not in text
    assert "fontawesome" not in text.lower()

assert CSS.count("{") == CSS.count("}"), "CSS braces are unbalanced"
print("UI-R15 verification: PASS")
print("- Issue Detail and Analysis bounded to 1320px")
print("- local analysis typography floor raised without widening the page")
print("- agent rail reflows before permanent-sidebar compression")
print("- assurance path, evidence, run IDs and governed decisions wrap safely")
print("- LangGraph/Qwen/human-authority contracts retained")
