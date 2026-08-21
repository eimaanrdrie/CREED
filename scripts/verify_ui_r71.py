from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
COMPONENTS = ROOT / "frontend/components"
CSS = (ROOT / "frontend/app/globals.css").read_text(encoding="utf-8")
DESIGN = (ROOT / "frontend/DESIGN.md").read_text(encoding="utf-8")
NOTES = (ROOT / "UI_R71_NOTES.md").read_text(encoding="utf-8")

FILES = {
    name: (COMPONENTS / name).read_text(encoding="utf-8")
    for name in [
        "final-dashboard.tsx",
        "issues-workspace.tsx",
        "issue-capsule-form.tsx",
        "issue-detail-workspace.tsx",
        "change-radar-workspace.tsx",
        "knowledge-workspace.tsx",
        "recalls-workspace.tsx",
        "audit-workspace.tsx",
        "ai-runtime-console.tsx",
        "analysis-shell.tsx",
    ]
}

# R71 removes route/subsection eyebrow primitives; semantic labels elsewhere remain untouched.
for name, source in FILES.items():
    assert 'className="eyebrow"' not in source, f"R71 eyebrow still rendered in {name}"

for token in [
    "Assurance control plane",
    '<div className="eyebrow">Cases</div>',
    '<div className="eyebrow">New issue</div>',
    'className="eyebrow">CASE RECORD',
    'className="eyebrow">EVIDENCE',
    'className="eyebrow">RECALL',
    'className="eyebrow">AUDIT TRAIL',
    'className="eyebrow">AI Runtime',
    'className="eyebrow">Live proof',
    'className="eyebrow">Execution proof',
    'className="eyebrow">Selected execution',
]:
    assert token not in "\n".join(FILES.values()), f"R71 redundant eyebrow survived: {token}"

# Removed labels that carried non-redundant information must retain that information.
assert 'case-hero-meta-r71' in FILES["issue-detail-workspace.tsx"]
assert '<strong>{sourceId}</strong>' in FILES["issue-detail-workspace.tsx"]

# Header/count/runtime pills become quiet inline metadata, not decorative SignalChip/StateBadge pills.
for token in [
    'className="editorial-meta-r71">{filtered.length} visible',
    'LOCAL REPOSITORY · {documents.length ? "READY" : "EMPTY"}',
    'audit-head-state-r44 editorial-meta-group-r71',
    'runtime-hero-meta-r71 editorial-meta-group-r71',
    '{recent.length} shown</span>',
    'runtime-state-inline-r71',
    'Last proof {formatMs(lastSuccessful.duration_ms)}</span>',
]:
    assert token in "\n".join(FILES.values()), f"Missing R71 inline metadata contract: {token}"

RUNTIME = FILES["ai-runtime-console.tsx"]
assert "SignalChip" not in RUNTIME, "AI Runtime decorative SignalChip usage should be removed in R71"
assert 'className={`runtime-state-r09' not in RUNTIME, "AI Runtime state remains pill-styled"

# Semantic compact state encoding remains in dense operational surfaces.
assert '<SignalChip tone={severityTone(issue.severity)}>' in FILES["issues-workspace.tsx"]
assert '<SignalChip tone="ok" icon={CheckCircle2}>Structured</SignalChip>' in FILES["analysis-shell.tsx"]
assert 'findingTone(selected.finding?.type)' in FILES["analysis-shell.tsx"]

for token in [
    "UI-R71 — Remove Hero Eyebrows + Decorative Pill Chips",
    ".editorial-meta-r71,",
    ".runtime-state-inline-r71,",
    ".case-hero-meta-r71 {",
    ".runtime-hero-meta-r71 {",
]:
    assert token in CSS, f"Missing R71 CSS contract: {token}"

assert "## UI-R71 — Editorial Header + Metadata Distillation" in DESIGN
assert "No sidebar active-state/accent treatment" in NOTES
assert "No off-white token or palette migration" in NOTES

# Explicitly protect later approval-gated tracks.
for future_hex in ["#F3EDE3", "#A8B5C3", "#7D8A98", "#7CC7D9", "#6FBF9E", "#D6A86B", "#C96B6B"]:
    assert future_hex not in CSS, f"R71 must not migrate future palette token {future_hex}"

# Approved Analysis runtime/governance wiring remains unchanged.
ANALYSIS = FILES["analysis-shell.tsx"]
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
    assert token in ANALYSIS, f"R71 regressed approved Analysis/runtime contract: {token}"
for label in ["Case Context", "Evidence", "Investigation", "Human Decision"]:
    assert label in ANALYSIS
assert "analysis-path-r55 { display:none!important; }" in CSS

AUDIT = FILES["audit-workspace.tsx"]
assert "const AUDIT_PAGE_SIZE = 6" in AUDIT
assert "audit-pagination-r48" in AUDIT
assert not (ROOT / "frontend/app/demo").exists(), "Demo route must remain removed"

# Lucide-only active icon policy and basic CSS/source integrity.
for path in (ROOT / "frontend").rglob("*.tsx"):
    source = path.read_text(encoding="utf-8")
    assert "<svg" not in source.lower(), f"Raw SVG found in {path}"
    assert "react-icons" not in source
    assert "@heroicons" not in source
    assert "fontawesome" not in source.lower()

assert CSS.count("{") == CSS.count("}"), "CSS braces are unbalanced"
print("UI-R71 verifier: PASS")
print("- redundant route/subsection eyebrows removed")
print("- decorative header/count/runtime pills distilled to inline metadata")
print("- semantic operational badges retained where state encoding is necessary")
print("- R70 Analysis/runtime/governance contracts, R48 Audit pagination and Demo removal preserved")
print("- R72 sidebar, R73 layout and R74 palette work not started")
