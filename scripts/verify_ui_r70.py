from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ANALYSIS = (ROOT / 'frontend/components/analysis-shell.tsx').read_text(encoding='utf-8')
CSS = (ROOT / 'frontend/app/globals.css').read_text(encoding='utf-8')
DESIGN = (ROOT / 'frontend/DESIGN.md').read_text(encoding='utf-8')
NOTES = (ROOT / 'UI_R70_NOTES.md').read_text(encoding='utf-8')

for token in [
    'analysis-r68 analysis-r69 analysis-r70',
    'AnalysisWorkspaceNavigator',
    '<h2>Agent Execution Task</h2>',
    'case-context-action-r63 verify',
    'case-context-action-r63 rerun',
    'analysis-radar-action-r63-rev1',
    'evidence-open-source-r65',
    'authority-choice-r53 authority-choice-r59 authority-choice-r67',
]:
    assert token in ANALYSIS, f'Missing R70 Analysis contract: {token}'

for token in [
    'UI-R70 — Analysis Responsive + Pixel Polish Closure',
    '.analysis-r70 {',
    '--analysis-mobile-gutter:12px',
    '@container analysis-workbench (max-width:1160px)',
    '@container analysis-workbench (max-width:820px)',
    '@container analysis-workbench (max-width:620px)',
    '@container analysis-workbench (max-width:430px)',
    '.analysis-r70 .analysis-workspace-tabs-r62',
    'scroll-snap-type:x proximity',
    '.analysis-r70 .case-context-actions-r56',
    '.analysis-r70 .authority-submit-r67 .primary-btn',
    'overflow-wrap:anywhere',
]:
    assert token in CSS, f'Missing R70 CSS contract: {token}'

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
    assert token in ANALYSIS, f'R70 regressed approved runtime wiring: {token}'

for label in ['Case Context', 'Evidence', 'Investigation', 'Human Decision']:
    assert label in ANALYSIS
assert 'analysis-path-r55 { display:none!important; }' in CSS
assert 'Analysis responsive + pixel polish closure' in DESIGN
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
print('UI-R70 verifier: PASS')
print('- responsive Analysis closure across desktop/laptop/mobile')
print('- four-workspace R62 IA and Agent Execution Task preserved')
print('- long dynamic proof values hardened against overflow')
print('- approved runtime/governance wiring preserved')
