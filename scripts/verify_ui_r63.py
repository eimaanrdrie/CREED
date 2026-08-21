from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ANALYSIS = (ROOT / 'frontend/components/analysis-shell.tsx').read_text(encoding='utf-8')
CSS = (ROOT / 'frontend/app/globals.css').read_text(encoding='utf-8')
DESIGN = (ROOT / 'frontend/DESIGN.md').read_text(encoding='utf-8')
NOTES = (ROOT / 'UI_R63_NOTES.md').read_text(encoding='utf-8')

for token in [
    'analysis-r63',
    'case-context-action-r63 verify compact',
    'case-context-action-r63 rerun compact',
    '<p className="case-source-excerpt-r56">{issue.description}</p>',
    'AnalysisWorkspaceNavigator',
    'Agent Execution Task',
]:
    assert token in ANALYSIS, f'Missing R63 Analysis contract: {token}'

# The Case Context actions must no longer inherit the legacy light compact
# secondary-button rule that produced the low-contrast screenshot state.
context_block = ANALYSIS[ANALYSIS.index('case-context-pane-r56 ai'):ANALYSIS.index('case-context-empty-r56') + len('case-context-empty-r56')]
assert 'className="secondary-btn compact"' not in context_block

for token in [
    'UI-R63 — CASE CONTEXT READABILITY + ACTION CONTRAST',
    '.analysis-r63 .case-source-excerpt-r56',
    'display:block;',
    '-webkit-line-clamp:unset;',
    'white-space:pre-wrap;',
    '.analysis-r63 .case-context-action-r63.verify',
    'background:var(--azure);',
    '.analysis-r63 .case-context-action-r63.rerun',
    '.analysis-r63 .case-context-action-r63:disabled',
    'opacity:1;',
]:
    assert token in CSS, f'Missing R63 CSS contract: {token}'

# Approved runtime wiring remains untouched.
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
    assert token in ANALYSIS, f'R63 regressed approved runtime wiring: {token}'

assert 'human-supplied issue description is shown in full' in DESIGN
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
print('UI-R63 verifier: PASS')
print('- full human source description is default-visible in Case Context')
print('- Verify/Re-run use dark-theme-native Analysis action states')
print('- disabled Re-run remains legible while existing runtime guard remains intact')
print('- approved R62 workspace navigation and backend wiring preserved')
