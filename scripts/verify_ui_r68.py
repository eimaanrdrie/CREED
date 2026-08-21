from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ANALYSIS = (ROOT / 'frontend/components/analysis-shell.tsx').read_text(encoding='utf-8')
CSS = (ROOT / 'frontend/app/globals.css').read_text(encoding='utf-8')
DESIGN = (ROOT / 'frontend/DESIGN.md').read_text(encoding='utf-8')
NOTES = (ROOT / 'UI_R68_NOTES.md').read_text(encoding='utf-8')

for token in [
    'analysis-r68',
    '<h2>Agent Execution Task</h2>',
    'execution-current-r60 execution-current-r68',
    '<span>CURRENT TASK</span>',
    'execution-current-meta-r68',
    'const currentStatus = current ? executionStatusLabel(current) : executionRunStatusLabel(run.status);',
    'const currentDuration = current?.duration_ms != null ? formatDuration(current.duration_ms) : "—";',
    'function executionRunStatusLabel(status:string)',
    '<ExecutionTimeline steps={run.steps} />',
    '<ExecutionProofDetails steps={run.steps} />',
    'safeRuntimeError(run.error)',
]:
    assert token in ANALYSIS, f'Missing R68 Analysis contract: {token}'

# Default current block must not repeat explanatory prose.
start = ANALYSIS.index('function ExecutionRail(')
end = ANALYSIS.index('\nfunction executionRunStatusLabel(', start)
block = ANALYSIS[start:end]
assert 'currentNote' not in block
assert 'Awaiting human decision.' not in block
assert 'GraphInterrupt(' not in block

# Existing truthful execution wiring remains.
for token in [
    'step.status === "RUNNING"',
    'step.status === "WAITING_HUMAN"',
    'step.status === "COMPLETED"',
    'step.status === "FAILED"',
    'run.graph_run_id',
    'step.duration_ms',
    'executionStepFacts(step)',
]:
    assert token in ANALYSIS, f'R68 regressed execution telemetry: {token}'

for token in [
    'UI-R68 — Agent Execution Task Refinement',
    '.analysis-r68 {',
    '--analysis-rail-width:224px',
    '.analysis-r68 .execution-current-r68',
    '.analysis-r68 .execution-current-meta-r68',
    '.analysis-r68 .execution-counts-r60',
    '.analysis-r68 .execution-timeline-r60',
    '.analysis-r68 .execution-step-r60',
    '.analysis-r68 .execution-details-r60 > summary',
    '@container analysis-workbench (max-width:1160px)',
    '@container analysis-workbench (max-width:620px)',
]:
    assert token in CSS, f'Missing R68 CSS contract: {token}'

for token in [
    'startAnalysisRun(issue.id)',
    'runIssueUnderstanding(issue.id)',
    'analysisRunEventsUrl(run.graph_run_id',
    'getRunEvidence(run.graph_run_id)',
    'getImpact(run.graph_run_id)',
    'getRunInvestigations(run.graph_run_id)',
    'getHumanReview(run.graph_run_id)',
    'resumeHumanReview(run.graph_run_id',
]:
    assert token in ANALYSIS, f'R68 regressed approved runtime wiring: {token}'

assert 'Agent Execution Task refinement' in DESIGN
assert 'No backend source file was changed' in NOTES
assert 'UI-R69' in NOTES
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
print('UI-R68 verifier: PASS')
print('- Agent Execution Task is the single compact lifecycle authority')
print('- current task shows real state + duration without repeated prose')
print('- execution details remain progressive disclosure')
print('- approved runtime/governance wiring preserved')
