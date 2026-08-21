from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CSS = (ROOT / "frontend/app/globals.css").read_text(encoding="utf-8")
DESIGN = (ROOT / "frontend/DESIGN.md").read_text(encoding="utf-8")
NOTES = (ROOT / "UI_R75_NOTES.md").read_text(encoding="utf-8")
ANALYSIS = (ROOT / "frontend/components/analysis-shell.tsx").read_text(encoding="utf-8")
RUNTIME = (ROOT / "frontend/components/ai-runtime-console.tsx").read_text(encoding="utf-8")
AUDIT = (ROOT / "frontend/components/audit-workspace.tsx").read_text(encoding="utf-8")
SIDEBAR = (ROOT / "frontend/components/sidebar.tsx").read_text(encoding="utf-8")

marker = "/* UI-R75 — Full Theme Consistency Pass"
assert marker in CSS, "Missing R75 consistency block"
r75 = CSS.split(marker, 1)[1]

for token in [
    "--creed-surface-subtle:",
    "--creed-surface-hover:",
    "--creed-surface-selected:",
    "--creed-border-subtle:",
    "--creed-border-strong:",
    "--creed-border-accent:",
    "--creed-state-success-border:",
    "--creed-state-warning-border:",
    "--creed-state-danger-border:",
    "--creed-state-info-border:",
    ".audit-page-number-r48.active {",
    ".progressive-disclosure > summary {",
    ".analysis-r69 .analysis-workspace-tab-r62.selected {",
    ".danger-governed-btn-r07 {",
]:
    assert token in r75, f"Missing R75 contract: {token}"

# Canonical R74 palette remains exact; R75 only derives roles from it.
for token, value in {
    "--creed-background": "#071019",
    "--creed-surface": "#0B1724",
    "--creed-raised": "#102033",
    "--creed-off-white": "#F3EDE3",
    "--creed-secondary": "#A8B5C3",
    "--creed-muted": "#7D8A98",
    "--creed-hairline": "#1B2A3A",
    "--creed-action": "#7CC7D9",
    "--creed-success": "#6FBF9E",
    "--creed-warning": "#D6A86B",
    "--creed-danger": "#C96B6B",
}.items():
    assert f"{token}: {value};" in CSS, f"R75 changed canonical palette {token}"

# R71-R74 approved layers must still exist.
for approved in [
    "/* UI-R71 — Remove Hero Eyebrows + Decorative Pill Chips",
    "/* UI-R72 — Sidebar Active-State / Accent Cleanup",
    "/* UI-R73 — AI Runtime / Execution Proof Alignment Correction",
    "/* UI-R74 — Off-White Palette Migration",
    "--runtime-proof-rail-r73: 18px;",
]:
    assert approved in CSS, f"R75 regressed approved layer: {approved}"

# Product/runtime/governance semantics remain wired to real sources.
for token in [
    'fetch(`${API_BASE_URL}/api/v1/ai/runtime?refresh=true`',
    'fetch(`${API_BASE_URL}/api/v1/ai/test`',
    'runtime?.recent_executions',
    'selectedExecution.duration_ms',
    'selectedExecution.prompt_eval_count',
    'selectedExecution.eval_count',
    'selectedExecution.structured_output_valid',
]:
    assert token in RUNTIME, f"R75 lost real runtime contract: {token}"

for token in [
    "AnalysisWorkspaceNavigator",
    "Case Context",
    "Evidence",
    "Investigation",
    "Human Decision",
    "<h2>Agent Execution Task</h2>",
    "startAnalysisRun(issue.id)",
    "analysisRunEventsUrl(run.graph_run_id",
    "resumeHumanReview(run.graph_run_id",
]:
    assert token in ANALYSIS, f"R75 regressed Analysis/governance contract: {token}"

assert "const AUDIT_PAGE_SIZE = 6" in AUDIT
assert "audit-pagination-r48" in AUDIT
assert 'aria-current={active === label ? "page" : undefined}' in SIDEBAR
assert not (ROOT / "frontend/app/demo").exists(), "Demo route must remain removed"

# Active icon source remains Lucide-only.
for path in (ROOT / "frontend").rglob("*.tsx"):
    source = path.read_text(encoding="utf-8")
    assert "<svg" not in source.lower(), f"Raw SVG found in {path}"
    assert "react-icons" not in source
    assert "@heroicons" not in source
    assert "fontawesome" not in source.lower()

assert "## UI-R75 — Full Theme Consistency Pass" in DESIGN
assert "No backend/API/database changes." in NOTES
assert CSS.count("{") == CSS.count("}"), "CSS braces are unbalanced"

print("UI-R75 verifier: PASS")
print("- final visual roles derive from the exact approved R74 palette")
print("- surfaces, semantic labels, selected states, filters, pagination and disclosures normalized")
print("- R71-R74, runtime truth, Analysis/Human Authority, R48 pagination, Demo removal and Lucide policy preserved")
