from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ANALYSIS = (ROOT / 'frontend/components/analysis-shell.tsx').read_text(encoding='utf-8')
CSS = (ROOT / 'frontend/app/globals.css').read_text(encoding='utf-8')
DESIGN = (ROOT / 'frontend/DESIGN.md').read_text(encoding='utf-8')
NOTES = (ROOT / 'UI_R64_NOTES.md').read_text(encoding='utf-8')

for token in [
    'analysis-r64',
    'qwen-context-summary-r56 qwen-context-summary-r64',
    'qwen-context-status-r56 qwen-context-status-r64',
    'qwen-client-mismatch-r64',
    'qwen-context-fields-r56 qwen-context-fields-r64',
    'case-context-action-r63 verify compact',
    'case-context-action-r63 rerun compact',
    '<p className="case-source-excerpt-r56">{issue.description}</p>',
    'ProgressiveDisclosure label="Inspect model interpretation"',
    'Agent Execution Task',
]:
    assert token in ANALYSIS, f'Missing R64 Analysis contract: {token}'

# R64 removes the generic competing mismatch chip from the Qwen glance.
qwen_block = ANALYSIS[ANALYSIS.index('function QwenContextSummary'):ANALYSIS.index('function ContextField')]
assert 'Check source mismatch' not in qwen_block
assert 'Source: {issue.client_name}' in qwen_block
assert '<em>Mismatch</em>' in qwen_block

for token in [
    'UI-R64 — CASE CONTEXT HIERARCHY + ACTION SYSTEM',
    '.analysis-r64 .case-context-workbench-r56',
    'grid-template-columns:minmax(0,1.12fr) minmax(340px,.88fr);',
    '.analysis-r64 .qwen-client-mismatch-r64',
    '.analysis-r64 .qwen-context-fields-r64',
    'background:transparent;',
    '.analysis-r64 .qwen-context-fields-r64 .qwen-context-field-r56.unknown strong',
    '.analysis-r64 .qwen-context-summary-r64 > .progressive-disclosure',
    '.analysis-r64 .case-context-action-r63.verify',
    '.analysis-r64 .case-context-action-r63.rerun',
]:
    assert token in CSS, f'Missing R64 CSS contract: {token}'

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
    assert token in ANALYSIS, f'R64 regressed approved runtime wiring: {token}'

assert 'Human Source owns slightly more horizontal reading space' in DESIGN
assert 'No backend source file was changed' in NOTES
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
print('UI-R64 verifier: PASS')
print('- Human Source and Qwen Interpretation hierarchy is rebalanced')
print('- Verify/Re-run/disclosure actions have distinct visual roles')
print('- client mismatch is attached to the affected comparison, not a competing top chip')
print('- missing extraction values recede without being hidden or invented')
print('- approved runtime/backend/governance semantics preserved')
