from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ANALYSIS = (ROOT / 'frontend/components/analysis-shell.tsx').read_text(encoding='utf-8')
CSS = (ROOT / 'frontend/app/globals.css').read_text(encoding='utf-8')
DESIGN = (ROOT / 'frontend/DESIGN.md').read_text(encoding='utf-8')
NOTES = (ROOT / 'UI_R61_NOTES.md').read_text(encoding='utf-8')

required_analysis = [
    'analysis-r61',
    'description?:string',
    '{description ? <p>{description}</p> : null}',
    '<AnalysisZone index="01" title="Case context">',
    '<AnalysisZone index="02" title="Evidence">',
    '<AnalysisZone index="03" title="Investigation">',
    '<AnalysisZone index="04" title="Human decision">',
    'Awaiting human decision.',
    'Choose outcome',
    'Separate human approval is required before reuse.',
    'Ranking and content seals do not establish correctness or approval.',
]
missing = [token for token in required_analysis if token not in ANALYSIS]
assert not missing, f'Missing R61 Analysis contract: {missing}'

required_css = [
    'UI-R61 — Full Analysis Adapt + Polish Closure',
    '.analysis-r61 {',
    '--analysis-rail-width:246px;',
    '.analysis-r61 .analysis-zone-r49 {',
    'border-top:1px solid',
    '.analysis-r61 .analysis-zone-body-r49 {',
    '.analysis-investigation-workbench-r58',
    '.human-decision-focus-r59',
    '.analysis-r61 .execution-panel-r60',
    '@container analysis-workbench (max-width:1080px)',
    '@container analysis-workbench (max-width:820px)',
    '@container analysis-workbench (max-width:620px)',
    'overflow-wrap:anywhere',
]
missing = [token for token in required_css if token not in CSS]
assert not missing, f'Missing R61 CSS contract: {missing}'

# R61 must remove visible zone helper copy while preserving prior verifier lineage only in comments.
for visible in [
    '<AnalysisZone index="01" title="Case context" description=',
    '<AnalysisZone index="02" title="Evidence" description=',
    '<AnalysisZone index="03" title="Investigation" description=',
    '<AnalysisZone index="04" title="Human decision" description=',
]:
    assert visible not in ANALYSIS, f'R61 still renders a zone helper description: {visible}'

# Approved real execution wiring must remain intact.
for token in [
    'startAnalysisRun(issue.id)',
    'runIssueUnderstanding(issue.id)',
    'analysisRunEventsUrl(run.graph_run_id',
    'getRunEvidence(run.graph_run_id)',
    'getImpact(run.graph_run_id)',
    'getRunInvestigations(run.graph_run_id)',
    'resumeHumanReview(run.graph_run_id',
    'step.status === "WAITING_HUMAN"',
    'run.status === "WAITING_HUMAN"',
]:
    assert token in ANALYSIS, f'R61 regressed approved Analysis wiring: {token}'

# No return of the raw runtime payload problem that R60 removed.
start = ANALYSIS.index('function ExecutionRail({ run, streamState }')
end = ANALYSIS.index('\nfunction AnalysisZone(', start)
rail = ANALYSIS[start:end]
assert 'output_summary' not in rail
assert '<AgentSteps' not in rail
assert 'current?.task' not in rail

assert 'ADAPT → POLISH' in DESIGN
assert 'R55–R61' in NOTES
assert 'No backend source file' in NOTES

# Product invariants.
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
print('UI-R61 verifier: PASS')
print('- major Analysis zones flattened into one operating flow')
print('- redundant default-visible zone helper copy removed')
print('- execution rail adapts before the main task becomes cramped')
print('- long dynamic proof containment hardened across Analysis')
print('- approved Qwen/LangGraph/Human Authority wiring preserved')
