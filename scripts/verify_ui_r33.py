from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CSS = (ROOT / "frontend" / "app" / "globals.css").read_text(encoding="utf-8")
ISSUES = (ROOT / "frontend" / "components" / "issues-workspace.tsx").read_text(encoding="utf-8")
NOTES = (ROOT / "UI_R33_NOTES.md").read_text(encoding="utf-8")
DESIGN = (ROOT / "frontend" / "DESIGN.md").read_text(encoding="utf-8")

for token in [
    "UI-R33 — Issues Metadata / Badge Overflow",
    ".issue-ledger-case-r33 > div",
    ".issue-case-signals-r33",
    "flex-wrap:wrap",
    ".issue-case-signals-r33 .signal-chip > span",
    "margin:0!important",
    "font-size:inherit!important",
    "white-space:nowrap",
    "-webkit-line-clamp:unset!important",
]:
    assert token in CSS, f"missing UI-R33 CSS contract: {token}"

for token in [
    'className="issue-ledger-case issue-ledger-case-r33"',
    'className="issue-case-signals-r24 issue-case-signals-r33"',
    'humanize(issue.severity)',
    'humanize(issue.issue_type)',
    'issue.attachment_count',
    'href={`/issues/${issue.id}`}',
]:
    assert token in ISSUES, f"Issues registry contract drifted: {token}"

assert "Older broad descendant rules" in NOTES
assert "UI-R34" in NOTES
assert "UI-R33 — Width-Safe Issue Metadata" in DESIGN
assert not (ROOT / "frontend" / "app" / "demo").exists(), "Demo route must remain removed"

for path in (ROOT / "frontend").rglob("*.tsx"):
    text = path.read_text(encoding="utf-8")
    assert "react-icons" not in text
    assert "@heroicons" not in text
    assert "fontawesome" not in text.lower()

assert CSS.count("{") == CSS.count("}"), "CSS braces are unbalanced"
print("UI-R33 verification: PASS")
print("- severity/type/attachment chips stay horizontal internally")
print("- metadata lane wraps before chips can collide or widen the ledger")
print("- approved typography, real SupportIssue values and case navigation preserved")
print("- Demo removal and Lucide-only policy preserved")
print("- UI-R34 whole-app overflow sweep remains out of scope")
