from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ANALYSIS = (ROOT / 'frontend/components/analysis-shell.tsx').read_text(encoding='utf-8')
CSS = (ROOT / 'frontend/app/globals.css').read_text(encoding='utf-8')
DESIGN = (ROOT / 'frontend/DESIGN.md').read_text(encoding='utf-8')
NOTES = (ROOT / 'UI_R66_NOTES.md').read_text(encoding='utf-8')

for token in [
    'analysis-r66',
    'investigation-matrix-head-r58 investigation-matrix-head-r66',
    'investigation-matrix-row-r58 investigation-matrix-row-r66',
    '<span>Candidate</span><span>Priority</span><span>AI finding</span><span>Human</span>',
    'investigation-selected-head-r58 investigation-selected-head-r66',
    'investigation-selected-signals-r58 investigation-selected-signals-r66',
    'aria-label="Selected implementation summary"',
    'investigation-focus-grid-r58 investigation-focus-grid-r66',
    'Priority drivers',
    'ProgressiveDisclosure label="All signals"',
    'ProgressiveDisclosure label="Inspect AI analysis"',
    'ProgressiveDisclosure label="Inspect proof" meta={`${evidenceRefs.length} evidence refs`',
    'analysis-radar-action-r63-rev1',
    'Priority ≠ verdict',
]:
    assert token in ANALYSIS, f'Missing R66 Analysis contract: {token}'

start = ANALYSIS.index('function InvestigationWorkbench(')
end = ANALYSIS.index('\nfunction humanizeImpactSignal', start)
block = ANALYSIS[start:end]

# R66 removes the decorative matrix arrow and the third default-visible Evidence
# panel. Evidence references remain available only through Inspect proof.
assert '<ArrowRight size={14} aria-hidden="true" />' not in block, 'Decorative candidate arrow remains in R66'
assert block.count('className="investigation-focus-r58 investigation-focus-r66"') == 2, 'R66 should expose only Priority drivers + AI finding by default'
proof_open = block.index('<ProgressiveDisclosure label="Inspect proof"')
assert block.index('Evidence references') > proof_open, 'Evidence references leaked before Inspect proof'
assert 'investigation-evidence-preview-r58' not in block, 'Default-visible evidence IDs remain in Investigation'
assert '<span>SELECTED</span>' not in block, 'Redundant SELECTED label remains visible'

for token in [
    'UI-R66 — Investigation Comparison Matrix refinement',
    '.analysis-r66 .investigation-matrix-head-r58',
    'grid-template-columns:minmax(220px,1.55fr) minmax(116px,.68fr) minmax(180px,1.15fr) minmax(120px,.72fr);',
    '.analysis-r66 .investigation-matrix-row-r58.selected',
    'border-left-color:var(--azure);',
    '.analysis-r66 .investigation-selected-head-r58',
    '.analysis-r66 .investigation-selected-signals-r58',
    '.analysis-r66 .investigation-focus-grid-r58',
    'grid-template-columns:minmax(0,.9fr) minmax(0,1.1fr);',
    '-webkit-line-clamp:2;',
    '@container analysis-workbench (max-width:760px)',
]:
    assert token in CSS, f'Missing R66 CSS contract: {token}'

for token in [
    'startAnalysisRun(issue.id)',
    'runIssueUnderstanding(issue.id)',
    'analysisRunEventsUrl(run.graph_run_id',
    'getRunEvidence(run.graph_run_id)',
    'getImpact(run.graph_run_id)',
    'getRunInvestigations(run.graph_run_id)',
    'getHumanReview(run.graph_run_id)',
    'resumeHumanReview(run.graph_run_id',
    'Agent Execution Task',
]:
    assert token in ANALYSIS, f'R66 regressed approved runtime wiring: {token}'

assert 'Investigation comparison matrix refinement' in DESIGN
assert 'No backend source file was changed' in NOTES
assert 'UI-R67' in NOTES
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
print('UI-R66 verifier: PASS')
print('- candidate matrix reduced to four aligned facts with selected-state affordance')
print('- selected candidate defaults to top three priority drivers + bounded AI advisory')
print('- evidence IDs and full proof remain behind Inspect')
print('- approved Analysis runtime/governance wiring preserved')
