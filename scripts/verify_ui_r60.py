from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ANALYSIS = (ROOT / 'frontend/components/analysis-shell.tsx').read_text(encoding='utf-8')
CSS = (ROOT / 'frontend/app/globals.css').read_text(encoding='utf-8')
DESIGN = (ROOT / 'frontend/DESIGN.md').read_text(encoding='utf-8')
NOTES = (ROOT / 'UI_R60_NOTES.md').read_text(encoding='utf-8')

required_analysis = [
    'analysis-r60',
    'execution-panel-r60',
    'Run telemetry',
    'execution-current-r60',
    'Awaiting governed human decision.',
    'execution-run-id-r60',
    'execution-counts-r60',
    'ExecutionTimeline',
    'execution-timeline-r60',
    'executionStatusLabel',
    'ExecutionProofDetails',
    'Execution details',
    'executionStepFacts',
    'safeRuntimeError',
    'GraphInterrupt',
    'Persisted technical details remain available in Audit.',
]
missing = [token for token in required_analysis if token not in ANALYSIS]
assert not missing, f'Missing R60 analysis contract: {missing}'

start = ANALYSIS.index('function ExecutionRail({ run, streamState }')
end = ANALYSIS.index('\nfunction AnalysisZone(', start)
block = ANALYSIS[start:end]

# The telemetry rail must not repeat investigation/Qwen output summaries or raw task payloads.
assert 'output_summary' not in block, 'R60 rail still renders persisted output summaries'
assert 'current?.task' not in block, 'R60 rail still renders the raw current task string'
assert 'step.task' not in block, 'R60 timeline still renders raw step task strings'
assert '<AgentSteps' not in block, 'R60 retained the old AgentSteps rail'
assert 'DECISION AUTHORITY' not in block, 'R60 should not repeat Human Authority in telemetry rail'

# Lifecycle truth still comes directly from real backend states.
for token in [
    'step.status === "RUNNING"',
    'step.status === "WAITING_HUMAN"',
    'step.status === "COMPLETED"',
    'step.status === "FAILED"',
    'run.status === "WAITING_HUMAN"',
    'step.duration_ms',
    'run.graph_run_id',
]:
    assert token in block, f'R60 missing real lifecycle proof: {token}'

# Known safe operational facts only; arrays/long payloads stay out of the rail.
for token in [
    'model_used', 'confidence', 'evidence_count', 'searched_chunks',
    'method_version_ids', 'candidate_count', 'result_count', 'evidence_gap_count'
]:
    assert token in block, f'R60 missing bounded operational fact: {token}'

required_css = [
    'UI-R60 — Execution Proof Distillation + Hardening',
    '.analysis-r60 { --analysis-rail-width:258px; }',
    '.execution-panel-r60',
    '.execution-head-r60',
    '.execution-current-r60',
    '.execution-run-r60',
    '.execution-counts-r60',
    '.execution-timeline-r60',
    '.execution-step-r60',
    '.execution-details-r60',
    '.execution-facts-r60',
    '.execution-error-r60',
    '.analysis-r60 .analysis-rail-panel-r49 .agent-ledger-list-r04 { display:none; }',
    '.analysis-r60 .execution-authority-r54 { display:none; }',
    '@container analysis-workbench (max-width:980px)',
    '@container analysis-workbench (max-width:620px)',
]
missing = [token for token in required_css if token not in CSS]
assert not missing, f'Missing R60 CSS contract: {missing}'

assert 'DISTILL → HARDEN' in DESIGN
assert 'must never display `GraphInterrupt(...)`' in DESIGN
assert 'UI-R61' in NOTES
assert 'No nested execution-list scrollbar remains.' in NOTES

# Approved no-fake-AI / orchestration wiring remains present.
for token in [
    'startAnalysisRun(issue.id)',
    'runIssueUnderstanding(issue.id)',
    'analysisRunEventsUrl(run.graph_run_id',
    'getRunEvidence(run.graph_run_id)',
    'getImpact(run.graph_run_id)',
    'getRunInvestigations(run.graph_run_id)',
    'resumeHumanReview(run.graph_run_id',
]:
    assert token in ANALYSIS, f'R60 regressed approved Analysis wiring: {token}'

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
print('UI-R60 verifier: PASS')
print('- execution rail reduced to real backend telemetry')
print('- raw GraphInterrupt/task/output-summary text is not rendered')
print('- one progressive execution-details disclosure retains bounded proof')
print('- Human Authority duplication removed from the execution rail')
print('- approved no-fake-AI / LangGraph / Human Review wiring preserved')
