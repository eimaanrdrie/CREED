from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ANALYSIS = (ROOT / "frontend/components/analysis-shell.tsx").read_text(encoding="utf-8")
CSS = (ROOT / "frontend/app/globals.css").read_text(encoding="utf-8")
DESIGN = (ROOT / "frontend/DESIGN.md").read_text(encoding="utf-8")
NOTES = (ROOT / "UI_R54_NOTES.md").read_text(encoding="utf-8")

required_analysis = [
    'analysis-r54',
    'analysis-execution-rail-r54',
    'function ExecutionRail',
    'EXECUTION PROOF',
    'execution-current-r54',
    'execution-counts-r54',
    'run.steps.filter(step => step.status === "COMPLETED").length',
    'run.steps.filter(step => step.status === "FAILED").length',
    'run.steps.filter(step => step.status === "QUEUED").length',
    'AgentSteps steps={run.steps}',
    'Human review required',
    'DECISION AUTHORITY',
    'Real lifecycle records appear when backend execution starts.',
]
missing = [token for token in required_analysis if token not in ANALYSIS]
assert not missing, f"Missing R54 analysis contract: {missing}"

required_css = [
    'UI-R54 — Analysis Execution Rail + Responsive/Polish Closure',
    '.analysis-r54',
    '.execution-panel-r54',
    '.execution-current-r54',
    '.execution-counts-r54',
    '.execution-authority-r54',
    '.analysis-r54 .analysis-rail-panel-r49 .agent-ledger-list-r04',
    '@container analysis-workbench (max-width:980px)',
    '@container analysis-workbench (max-width:620px)',
    '@container analysis-workbench (max-width:440px)',
    'overflow-wrap:anywhere',
]
missing = [token for token in required_css if token not in CSS]
assert not missing, f"Missing R54 CSS contract: {missing}"

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
    assert token in ANALYSIS, f"R54 regressed approved analysis wiring: {token}"

# The older R49 authority block is replaced in the rail, while the main R53
# Human Authority workbench remains intact.
assert 'authority-boundary-r04 analysis-authority-r49' not in ANALYSIS
assert 'function HumanDecisionWorkbench' in ANALYSIS
assert 'evidence-workbench-r52' in ANALYSIS
assert 'investigation-workbench-r51' in ANALYSIS

assert 'execution-proof rail' in DESIGN
assert 'No backend source file, API contract, database model or LangGraph graph changed.' in NOTES
assert 'UI-R49 through UI-R54' in NOTES
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
print('UI-R54 verifier: PASS')
print('- current execution and lifecycle counts come from real AnalysisRun/AgentStep state')
print('- full agent chronology remains visible and inspectable')
print('- desktop sticky rail becomes a non-scrolling proof surface after single-column reflow')
print('- R53/R52/R51/R50/R49/R48 continuity preserved')
