from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ANALYSIS = (ROOT / "frontend/components/analysis-shell.tsx").read_text(encoding="utf-8")
CSS = (ROOT / "frontend/app/globals.css").read_text(encoding="utf-8")
DESIGN = (ROOT / "frontend/DESIGN.md").read_text(encoding="utf-8")
NOTES = (ROOT / "UI_R58_NOTES.md").read_text(encoding="utf-8")

required_analysis = [
    'analysis-r58',
    'analysis-investigation-workbench-r58',
    'CANDIDATE MATRIX',
    'Priority ≠ verdict',
    'Priority score, not a defect verdict.',
    'investigation-matrix-r58',
    'investigation-matrix-row-r58',
    'investigation-selected-r58',
    'Priority drivers',
    'topDrivers',
    'All signals',
    'Inspect AI analysis',
    'investigation-ai-clamp-r58',
    'evidenceRefs.slice(0, 3)',
    'Inspect proof',
    'Compare candidates, then inspect one.',
]
missing = [token for token in required_analysis if token not in ANALYSIS]
assert not missing, f"Missing R58 analysis contract: {missing}"

start = ANALYSIS.index('function InvestigationWorkbench({ run, impact, investigations }')
end = ANALYSIS.index('\nfunction humanizeImpactSignal', start)
block = ANALYSIS[start:end]

# Default view must remain concise: no more than top-three drivers and the full
# AI statement must also be available behind Inspect rather than only visible.
assert 'const topDrivers = explanations.slice(0, 3);' in block
assert 'const remainingDrivers = explanations.slice(3);' in block
all_signals_open = block.index('<ProgressiveDisclosure label="All signals"')
assert block.index('explanations.map', all_signals_open) > all_signals_open
ai_inspect_open = block.index('<ProgressiveDisclosure label="Inspect AI analysis"')
ai_statement_occurrences = [i for i in range(len(block)) if block.startswith('selectedInvestigation.finding.statement', i)]
assert len(ai_statement_occurrences) >= 2, 'Persisted AI statement must exist in glance and inspect layers'
assert any(i > ai_inspect_open for i in ai_statement_occurrences), 'Full AI analysis is not present behind Inspect'
proof_open = block.index('<ProgressiveDisclosure label="Inspect proof"')
assert block.index('Evidence references', proof_open) > proof_open, 'Complete evidence refs must remain proof content'

required_css = [
    'UI-R58 — Investigation Visual Matrix',
    '.analysis-investigation-workbench-r58',
    '.investigation-matrix-r58',
    '.investigation-matrix-row-r58',
    'min-height:58px',
    '.investigation-selected-r58',
    '.investigation-focus-grid-r58',
    '.investigation-driver-r58',
    '.investigation-ai-clamp-r58',
    '-webkit-line-clamp:3',
    '.investigation-proof-r58',
    '@container analysis-workbench (max-width:960px)',
    '@container analysis-workbench (max-width:700px)',
    '@container analysis-workbench (max-width:470px)',
]
missing = [token for token in required_css if token not in CSS]
assert not missing, f"Missing R58 CSS contract: {missing}"

# Approved real execution / governance wiring remains present.
for token in [
    'startAnalysisRun(issue.id)',
    'runIssueUnderstanding(issue.id)',
    'analysisRunEventsUrl(run.graph_run_id',
    'getRunEvidence(run.graph_run_id)',
    'getImpact(run.graph_run_id)',
    'getRunInvestigations(run.graph_run_id)',
    'getHumanReview(run.graph_run_id)',
    'resumeHumanReview(run.graph_run_id',
    'AI finding is advisory.',
    'AI investigates. Humans decide.',
]:
    assert token in ANALYSIS, f"R58 regressed approved Analysis wiring: {token}"

assert 'LAYOUT → TYPESET → DISTILL' in DESIGN
assert 'exact persisted evidence reference IDs' in NOTES
assert 'UI-R59' in NOTES
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
print('UI-R58 verifier: PASS')
print('- candidate comparison distilled into one visual matrix')
print('- top-three priority drivers, clamped AI finding and evidence count lead')
print('- full signal math, AI statement and complete evidence proof stay inspectable')
print('- approved Qwen/LangGraph/Human Authority wiring preserved')
