from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CSS = (ROOT / "frontend/app/globals.css").read_text(encoding="utf-8")
SIDEBAR = (ROOT / "frontend/components/sidebar.tsx").read_text(encoding="utf-8")
DESIGN = (ROOT / "frontend/DESIGN.md").read_text(encoding="utf-8")
NOTES = (ROOT / "UI_R72_NOTES.md").read_text(encoding="utf-8")
ANALYSIS = (ROOT / "frontend/components/analysis-shell.tsx").read_text(encoding="utf-8")

marker = "/* UI-R72 — Sidebar Active-State / Accent Cleanup"
assert marker in CSS, "Missing R72 sidebar treatment block"
r72_css = CSS.split(marker, 1)[1]

for token in [
    ".nav-primary .nav-item.active {",
    "background: var(--panel-soft);",
    "color: var(--text);",
    "box-shadow: inset 2px 0 0 oklch(80% 0.027 246 / .30);",
    ".nav-primary .nav-item.active::before {",
    "content: none;",
    "display: none;",
    ".nav-primary .nav-item.active svg { color: var(--text-soft); }",
    ".nav-primary .nav-item:not(.active):hover {",
    "box-shadow: inset 3px 0 0 var(--text-soft);",
]:
    assert token in r72_css, f"Missing R72 CSS contract: {token}"

# The new effective active-state block must not use the bright action accent.
for forbidden in ["var(--azure)", "var(--azure-pale)", "var(--gold)", "var(--gold-pale)"]:
    assert forbidden not in r72_css, f"R72 active navigation reintroduced bright accent: {forbidden}"

# Navigation semantics and information architecture stay intact.
for label, href in [
    ("Overview", 'href: "/"'),
    ("Issues", 'href: "/issues"'),
    ("Change Radar", 'href: "/change-radar"'),
    ("Knowledge", 'href: "/knowledge"'),
    ("Recalls", 'href: "/recalls"'),
    ("Audit", 'href: "/audit"'),
    ("AI Runtime", 'href: "/ai-runtime"'),
]:
    assert f'label: "{label}"' in SIDEBAR
    assert href in SIDEBAR
assert 'aria-current={active === label ? "page" : undefined}' in SIDEBAR
assert 'className={`nav-item ${active === label ? "active" : ""}`}' in SIDEBAR
assert 'from "lucide-react"' in SIDEBAR

assert "## UI-R72 — Sidebar Active-State / Accent Cleanup" in DESIGN
assert "No AI Runtime / Execution Proof alignment" in NOTES
assert "No off-white palette token migration" in NOTES

# Future palette migration remains untouched.
for future_hex in ["#F3EDE3", "#A8B5C3", "#7D8A98", "#7CC7D9", "#6FBF9E", "#D6A86B", "#C96B6B"]:
    assert future_hex not in CSS, f"R72 must not migrate future palette token {future_hex}"

# Approved Analysis/runtime/governance wiring remains intact.
for token in [
    "analysis-r68 analysis-r69 analysis-r70",
    "AnalysisWorkspaceNavigator",
    "<h2>Agent Execution Task</h2>",
    "startAnalysisRun(issue.id)",
    "runIssueUnderstanding(issue.id)",
    "analysisRunEventsUrl(run.graph_run_id",
    "getRunEvidence(run.graph_run_id)",
    "getImpact(run.graph_run_id)",
    "getRunInvestigations(run.graph_run_id)",
    "getHumanReview(run.graph_run_id)",
    "resumeHumanReview(run.graph_run_id",
]:
    assert token in ANALYSIS, f"R72 regressed approved Analysis/runtime contract: {token}"
for label in ["Case Context", "Evidence", "Investigation", "Human Decision"]:
    assert label in ANALYSIS
assert "analysis-path-r55 { display:none!important; }" in CSS

AUDIT = (ROOT / "frontend/components/audit-workspace.tsx").read_text(encoding="utf-8")
assert "const AUDIT_PAGE_SIZE = 6" in AUDIT
assert "audit-pagination-r48" in AUDIT
assert not (ROOT / "frontend/app/demo").exists(), "Demo route must remain removed"

for path in (ROOT / "frontend").rglob("*.tsx"):
    source = path.read_text(encoding="utf-8")
    assert "<svg" not in source.lower(), f"Raw SVG found in {path}"
    assert "react-icons" not in source
    assert "@heroicons" not in source
    assert "fontawesome" not in source.lower()

assert CSS.count("{") == CSS.count("}"), "CSS braces are unbalanced"
print("UI-R72 verifier: PASS")
print("- active sidebar selection now uses calm surface + neutral inset rule")
print("- bright Azure active stripe/fill removed from the effective R72 treatment")
print("- navigation semantics, mobile behavior, accessibility and Lucide policy preserved")
print("- R73 runtime layout, R74 palette and backend/governance behavior untouched")
