from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CSS = (ROOT / "frontend/app/globals.css").read_text(encoding="utf-8")
RUNTIME = (ROOT / "frontend/components/ai-runtime-console.tsx").read_text(encoding="utf-8")
DESIGN = (ROOT / "frontend/DESIGN.md").read_text(encoding="utf-8")
NOTES = (ROOT / "UI_R73_NOTES.md").read_text(encoding="utf-8")
ANALYSIS = (ROOT / "frontend/components/analysis-shell.tsx").read_text(encoding="utf-8")

marker = "/* UI-R73 — AI Runtime / Execution Proof Alignment Correction"
assert marker in CSS, "Missing R73 layout block"
r73_css = CSS.split(marker, 1)[1]

for token in [
    "--runtime-proof-rail-r73: 18px;",
    ".runtime-history-head-r30 {",
    "padding: 13px var(--runtime-proof-rail-r73);",
    ".runtime-execution-meta-r36 {",
    "grid-template-columns: minmax(58px, auto) minmax(0, auto);",
    "font-variant-numeric: tabular-nums;",
    ".runtime-selected-r30 {\n  padding: 0;",
    ".runtime-selected-glance-r30 {",
    "grid-template-columns: repeat(3, minmax(0, 1fr));",
    "border-radius: 0;",
    ".runtime-selected-r30 > .progressive-disclosure {\n  margin: 0;\n  border: 0;",
    ".runtime-detail-grid-r30 {",
    "grid-template-columns: repeat(3, minmax(0, 1fr));",
    "@container runtime-proof (max-width: 760px)",
    "--runtime-proof-rail-r73: 14px;",
]:
    assert token in r73_css, f"Missing R73 CSS contract: {token}"

# R73 must operate on the real persisted runtime data already wired into R72.
for token in [
    'fetch(`${API_BASE_URL}/api/v1/ai/runtime?refresh=true`',
    'fetch(`${API_BASE_URL}/api/v1/ai/test`',
    'runtime?.recent_executions',
    'selectedExecution.duration_ms',
    'selectedExecution.prompt_eval_count',
    'selectedExecution.eval_count',
    'selectedExecution.structured_output_valid',
    'selectedExecution.run_id',
    'selectedExecution.configured_model',
    'selectedExecution.actual_model',
    'selectedExecution.started_at',
    'selectedExecution.completed_at',
]:
    assert token in RUNTIME, f"R73 lost real runtime data contract: {token}"

# R71 distillation and R72 sidebar treatment remain present.
assert "runtime-state-inline-r71" in RUNTIME
assert "/* UI-R72 — Sidebar Active-State / Accent Cleanup" in CSS
assert "## UI-R73 — AI Runtime / Execution Proof Alignment Correction" in DESIGN
assert "No off-white palette token migration" in NOTES

# Future palette migration remains untouched.
for future_hex in ["#F3EDE3", "#A8B5C3", "#7D8A98", "#7CC7D9", "#6FBF9E", "#D6A86B", "#C96B6B"]:
    assert future_hex not in CSS, f"R73 must not migrate future palette token {future_hex}"

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
    assert token in ANALYSIS, f"R73 regressed approved Analysis/runtime contract: {token}"
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
print("UI-R73 verifier: PASS")
print("- Execution Proof uses one shared content rail")
print("- duration/timestamp metadata receives deliberate alignment")
print("- selected metrics and provenance are flattened out of nested card soup")
print("- R71/R72, Analysis architecture, runtime truth and governance contracts preserved")
print("- R74 palette migration not started")
