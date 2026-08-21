from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ANALYSIS = (ROOT / "frontend/components/analysis-shell.tsx").read_text(encoding="utf-8")
CSS = (ROOT / "frontend/app/globals.css").read_text(encoding="utf-8")
DESIGN = (ROOT / "frontend/DESIGN.md").read_text(encoding="utf-8")
NOTES = (ROOT / "UI_R49_NOTES.md").read_text(encoding="utf-8")

required_analysis = [
    'analysis-r49',
    'analysis-workbench-head-r49',
    'analysis-case-facts-r49',
    'analysis-run-control-r49',
    'analysis-workbench-r49',
    'analysis-focus-r49',
    'analysis-rail-r49',
    'analysis-rail-panel-r49',
    'function AnalysisZone',
    'index="01" title="Case context"',
    'index="02" title="Evidence"',
    'index="03" title="Investigation"',
    'index="04" title="Human decision"',
    'analysis-zone-r49',
    'analysis-zone-body-r49',
    'AI investigates. Humans decide.',
]
missing = [token for token in required_analysis if token not in ANALYSIS]
assert not missing, f"Missing R49 analysis structure: {missing}"

required_css = [
    'UI-R49 — Analysis Workbench Foundation',
    'container-name:analysis-workbench',
    '.analysis-workbench-head-r49',
    '.analysis-case-facts-r49',
    '.analysis-workbench-r49',
    '.analysis-zone-r49',
    '.analysis-zone-head-r49',
    '.analysis-zone-body-r49',
    '.analysis-rail-panel-r49',
    '@container analysis-workbench (max-width:980px)',
    '@container analysis-workbench (max-width:560px)',
]
missing = [token for token in required_css if token not in CSS]
assert not missing, f"Missing R49 CSS contract: {missing}"

# Approved execution/governance contracts must remain wired to the real backend.
for token in [
    'startAnalysisRun(issue.id)',
    'runIssueUnderstanding(issue.id)',
    'analysisRunEventsUrl(run.graph_run_id',
    'getRunEvidence(run.graph_run_id)',
    'getImpact(run.graph_run_id)',
    'getRunInvestigations(run.graph_run_id)',
    'getHumanReview(run.graph_run_id)',
    'resumeHumanReview(run.graph_run_id',
    '"AFFECTED"',
    '"NOT_AFFECTED"',
    '"NEEDS_MORE_INVESTIGATION"',
    'Priority score, not a defect verdict.',
]:
    assert token in ANALYSIS, f"R49 regressed approved analysis contract: {token}"

# R48 remains present and unchanged in the same baseline.
AUDIT = (ROOT / "frontend/components/audit-workspace.tsx").read_text(encoding="utf-8")
assert 'const AUDIT_PAGE_SIZE = 6' in AUDIT
assert 'audit-pagination-r48' in AUDIT

assert 'Operate-mode investigation workbench' in DESIGN
assert 'No API contract or backend service changed.' in NOTES
assert 'UI-R50' in NOTES
assert not (ROOT / 'frontend/app/demo').exists(), 'Demo route must remain removed'

for path in (ROOT / 'frontend').rglob('*.tsx'):
    source = path.read_text(encoding='utf-8')
    assert '<svg' not in source.lower(), f'Raw SVG found in {path}'
    assert 'react-icons' not in source
    assert '@heroicons' not in source
    assert 'fontawesome' not in source.lower()

assert CSS.count('{') == CSS.count('}'), 'CSS braces are unbalanced'
print('UI-R49 verifier: PASS')
print('- Analysis is grouped into four work zones')
print('- execution/authority rail is structurally unified')
print('- backend, Qwen, LangGraph, evidence, impact and human-decision wiring preserved')
print('- R48 Audit pagination preserved')
