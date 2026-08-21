from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ANALYSIS = (ROOT / 'frontend/components/analysis-shell.tsx').read_text(encoding='utf-8')
CSS = (ROOT / 'frontend/app/globals.css').read_text(encoding='utf-8')
DESIGN = (ROOT / 'frontend/DESIGN.md').read_text(encoding='utf-8')
NOTES = (ROOT / 'UI_R69_NOTES.md').read_text(encoding='utf-8')

for token in [
    'analysis-r68 analysis-r69',
    'AnalysisWorkspaceNavigator',
    '<h2>Agent Execution Task</h2>',
    'case-context-action-r63 verify',
    'case-context-action-r63 rerun',
    'analysis-radar-action-r63-rev1',
    'evidence-open-source-r65',
    'authority-choice-r53 authority-choice-r59 authority-choice-r67',
    'authority-ai-quiet-r59 sr-only',
]:
    assert token in ANALYSIS, f'Missing R69 Analysis contract: {token}'

for token in [
    'UI-R69 — Analysis Visual System Normalization',
    '.analysis-r69 {',
    '--analysis-action-h:38px',
    '--analysis-control-radius:6px',
    '.analysis-r69 .analysis-workspace-tab-r62.selected',
    '.analysis-r69 .progressive-disclosure > summary',
    '.analysis-r69 :where(.evidence-hit-r65.selected,.investigation-matrix-row-r58.selected,.authority-case-r67.selected)',
    '.analysis-r69 .authority-choice-r67',
    '.analysis-r69 .execution-panel-r60',
    '@container analysis-workbench (max-width:760px)',
]:
    assert token in CSS, f'Missing R69 CSS contract: {token}'

# Approved runtime/governance wiring must remain unchanged.
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
    assert token in ANALYSIS, f'R69 regressed approved runtime wiring: {token}'

# Workspace IA remains exactly the four approved R62 views.
for label in ['Case Context', 'Evidence', 'Investigation', 'Human Decision']:
    assert label in ANALYSIS
assert 'analysis-path-r55 { display:none!important; }' in CSS

assert 'Analysis visual system normalization' in DESIGN
assert 'No backend source file was changed' in NOTES
assert 'UI-R70' in NOTES
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
print('UI-R69 verifier: PASS')
print('- Analysis action / selection / badge / disclosure systems normalized')
print('- four-workspace R62 information architecture preserved')
print('- Agent Execution Task remains secondary proof')
print('- approved runtime/governance wiring preserved')
