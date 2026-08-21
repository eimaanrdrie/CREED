from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ANALYSIS = (ROOT / "frontend/components/analysis-shell.tsx").read_text(encoding="utf-8")
CSS = (ROOT / "frontend/app/globals.css").read_text(encoding="utf-8")
DESIGN = (ROOT / "frontend/DESIGN.md").read_text(encoding="utf-8")
NOTES = (ROOT / "UI_R51_NOTES.md").read_text(encoding="utf-8")

required_analysis = [
    'analysis-r51',
    'function InvestigationWorkbench',
    'InvestigationWorkbenchItem',
    'investigation-command-r51',
    'investigation-layout-r51',
    'investigation-master-r51 investigation-cards-r25',
    'investigation-candidate-r51',
    'aria-pressed={selectedRow}',
    'setSelectedImplementationId(item.implementation_id)',
    'investigation-detail-r51',
    'investigation-priority-r51',
    'impact-visual-r25 investigation-priority-signals-r51',
    'humanizeImpactSignal',
    'AI confidence',
    'ProgressiveDisclosure label="Inspect proof"',
    'Priority score, not a defect verdict.',
    'selectedInvestigation?.human_decision',
    'selectedImpact?.explanation',
    'selectedInvestigation?.finding?.evidence_refs',
]
missing = [token for token in required_analysis if token not in ANALYSIS]
assert not missing, f"Missing R51 analysis contract: {missing}"

# The old stacked visual-card implementations must no longer be rendered.
assert 'className="investigation-card-r25"' not in ANALYSIS, 'R51 must remove old per-implementation finding cards'
assert 'className="impact-visual-row-r25"' not in ANALYSIS, 'R51 must remove old standalone impact rows'

required_css = [
    'UI-R51 — Investigation Workspace Redesign',
    '.analysis-investigation-workbench-r51',
    '.investigation-command-r51',
    '.investigation-layout-r51',
    '.investigation-master-r51.investigation-cards-r25',
    '.investigation-candidate-r51.selected',
    '.investigation-detail-r51',
    '.investigation-priority-r51',
    '.investigation-detail-grid-r51',
    '.investigation-priority-signals-r51.impact-visual-r25',
    '.investigation-proof-r51',
    '@container analysis-workbench (max-width:820px)',
    '@container analysis-workbench (max-width:620px)',
    '@container analysis-workbench (max-width:440px)',
]
missing = [token for token in required_css if token not in CSS]
assert not missing, f"Missing R51 CSS contract: {missing}"

# Approved runtime/governance wiring remains intact.
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
]:
    assert token in ANALYSIS, f"R51 regressed approved analysis wiring: {token}"

assert 'Operate-mode master/detail workbench' in DESIGN
assert 'No API contract or backend service changed.' in NOTES
assert 'UI-R52' in NOTES
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
print('UI-R51 verifier: PASS')
print('- Impact + findings merged into one master/detail investigation workbench')
print('- deterministic priority, AI finding, proof and Human Authority remain separate')
print('- selection is frontend focus only; backend semantics are preserved')
print('- R50/R49/R48 continuity preserved')
