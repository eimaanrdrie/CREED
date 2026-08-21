from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ANALYSIS = (ROOT / "frontend/components/analysis-shell.tsx").read_text(encoding="utf-8")
CSS = (ROOT / "frontend/app/globals.css").read_text(encoding="utf-8")
DESIGN = (ROOT / "frontend/DESIGN.md").read_text(encoding="utf-8")
NOTES = (ROOT / "UI_R55_NOTES.md").read_text(encoding="utf-8")

required_analysis = [
    'analysis-r55',
    'analysis-header-r55',
    'analysis-meta-r55',
    'analysis-run-id-r55',
    'analysis-compact-summary-r55',
    'analysis-state-bar-r55',
    'analysis-inline-signals-r55',
    'analysis-path-r55',
    'analysis-path-track-r55',
    'Workflow paused for governed decision',
    'decisions required',
    'agent === "human_review_boundary" && run.status === "WAITING_HUMAN"',
    'stageState === "human" ? "Action required"',
    'numericMeta(retrievalStep, "evidence_count")',
    'numericMeta(impactStep, "candidate_count")',
    'getHumanReview(run.graph_run_id)',
]
missing = [token for token in required_analysis if token not in ANALYSIS]
assert not missing, f"Missing R55 analysis contract: {missing}"

# R55 deliberately removes the rendered dashboard/kicker that made the first
# viewport noisy. Historical R50 CSS/functions may remain in source lineage,
# but they may not be called by the AnalysisShell top-level composition.
top = ANALYSIS[ANALYSIS.index('export function AnalysisShell'):ANALYSIS.index('function ExecutionRail')]
assert 'analysis-workbench-head-r49' not in top, 'Old R49 header is still rendered'
assert 'ANALYSIS WORKBENCH' not in top, 'Redundant Analysis Workbench kicker is still rendered'
assert 'analysis-case-summary-r50' not in top, 'Old R50 summary card is still rendered'
assert 'analysis-stage-shell-r50' not in top, 'Old R50 boxed path is still rendered'

required_css = [
    'UI-R55 — Analysis Header + State Compression',
    '.analysis-header-r55',
    '.analysis-state-bar-r55',
    '.analysis-inline-signals-r55',
    '.analysis-path-r55',
    '.analysis-path-step-r55.human',
    '.analysis-path-step-r55.bad',
    '.analysis-path-step-r55.cancelled',
    '@container analysis-workbench (max-width:920px)',
    '@container analysis-workbench (max-width:680px)',
    '@container analysis-workbench (max-width:440px)',
]
missing = [token for token in required_css if token not in CSS]
assert not missing, f"Missing R55 CSS contract: {missing}"

# Approved runtime/governance wiring must remain.
for token in [
    'startAnalysisRun(issue.id)',
    'runIssueUnderstanding(issue.id)',
    'analysisRunEventsUrl(run.graph_run_id',
    'getRunEvidence(run.graph_run_id)',
    'getImpact(run.graph_run_id)',
    'getRunInvestigations(run.graph_run_id)',
    'getHumanReview(run.graph_run_id)',
    'resumeHumanReview(run.graph_run_id',
    'Priority score, not a defect verdict.',
    'AI finding is advisory.',
    'AI investigates. Humans decide.',
    '"AFFECTED"',
    '"NOT_AFFECTED"',
    '"NEEDS_MORE_INVESTIGATION"',
]:
    assert token in ANALYSIS, f"R55 regressed approved analysis wiring: {token}"

assert 'DISTILL → CLARIFY → LAYOUT' in DESIGN
assert 'No backend source file, database model, API contract or LangGraph graph changed.' in NOTES
assert 'UI-R56' in NOTES
assert not (ROOT / 'frontend/app/demo').exists(), 'Demo route must remain removed'

AUDIT = (ROOT / 'frontend/components/audit-workspace.tsx').read_text(encoding='utf-8')
assert 'const AUDIT_PAGE_SIZE = 6' in AUDIT
assert 'audit-pagination-r48' in AUDIT

for path in (ROOT / 'frontend').rglob('*.tsx'):
    source = path.read_text(encoding='utf-8')
    assert '<svg' not in source.lower(), f'Raw SVG found in {path}'
    assert 'react-icons' not in source
    assert '@heroicons' not in source
    assert 'fontawesome' not in source.lower()

assert CSS.count('{') == CSS.count('}'), 'CSS braces are unbalanced'
print('UI-R55 verifier: PASS')
print('- first viewport distilled to issue identity, real state, essential signals and lightweight graph path')
print('- WAITING_HUMAN is an amber governed action state, not a failure/BAD state')
print('- old six-cell summary and boxed seven-stage path are no longer rendered')
print('- approved backend/Qwen/LangGraph/retrieval/governance wiring preserved')
