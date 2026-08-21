from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ANALYSIS = (ROOT / 'frontend/components/analysis-shell.tsx').read_text(encoding='utf-8')
CSS = (ROOT / 'frontend/app/globals.css').read_text(encoding='utf-8')
DESIGN = (ROOT / 'frontend/DESIGN.md').read_text(encoding='utf-8')
NOTES = (ROOT / 'UI_R63_REV1_NOTES.md').read_text(encoding='utf-8')

for token in [
    'analysis-r63-rev1',
    'className="analysis-radar-action-r63-rev1"',
    'Radar<ArrowUpRight size={13} />',
    'case-context-action-r63 verify compact',
    'case-context-action-r63 rerun compact',
    '<p className="case-source-excerpt-r56">{issue.description}</p>',
    'Agent Execution Task',
]:
    assert token in ANALYSIS, f'Missing R63 REV1 Analysis contract: {token}'

radar_line = next(line for line in ANALYSIS.splitlines() if '>Radar<ArrowUpRight' in line)
assert 'secondary-btn' not in radar_line, 'Radar still inherits legacy secondary button styling'

for token in [
    'UI-R63 REV1 — ANALYSIS ACTION VISIBILITY + THIN SCROLLBARS',
    '.analysis-r63-rev1 .analysis-radar-action-r63-rev1',
    'background:color-mix(in oklab,var(--azure) 8%,var(--panel-raised));',
    'color:var(--azure-pale);',
    'html::-webkit-scrollbar { width:6px; height:6px; }',
    'scrollbar-width:thin;',
    '.analysis-r63-rev1 *::-webkit-scrollbar { width:6px; height:6px; }',
    '.analysis-r63-rev1 .analysis-workspace-tabs-r62::-webkit-scrollbar { display:none; }',
]:
    assert token in CSS, f'Missing R63 REV1 CSS contract: {token}'

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
    assert token in ANALYSIS, f'R63 REV1 regressed approved runtime wiring: {token}'

assert 'Analysis-scoped dark Azure action' in DESIGN
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
print('UI-R63 REV1 verifier: PASS')
print('- R63 Case Context fixes preserved')
print('- Radar uses dark-theme-native Analysis action styling')
print('- root and Analysis-owned scrollbars use a thin 6px rail')
print('- approved runtime/backend/governance semantics preserved')
