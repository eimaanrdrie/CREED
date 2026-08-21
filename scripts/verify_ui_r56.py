from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ANALYSIS = (ROOT / "frontend/components/analysis-shell.tsx").read_text(encoding="utf-8")
CSS = (ROOT / "frontend/app/globals.css").read_text(encoding="utf-8")
DESIGN = (ROOT / "frontend/DESIGN.md").read_text(encoding="utf-8")
NOTES = (ROOT / "UI_R56_NOTES.md").read_text(encoding="utf-8")

required_analysis = [
    'analysis-r56',
    'description="Source fact vs AI interpretation."',
    'case-context-workbench-r56',
    'SourceContextSummary issue={issue} run={run}',
    'case-context-pane-r56 ai',
    'HUMAN SOURCE',
    'Human supplied',
    'View original ticket',
    'ORIGINAL OBSERVATION',
    'AI INTERPRETATION',
    'Qwen understanding',
    'QwenContextSummary issue={issue} understanding={understanding}',
    'ContextField label="Product"',
    'ContextField label="Module"',
    'ContextField label="Issue type"',
    'ContextField label="Function"',
    'Inspect model interpretation',
    'Summary · keywords · runtime proof',
    'Source client',
    'differs from Qwen extraction',
]
missing = [token for token in required_analysis if token not in ANALYSIS]
assert not missing, f"Missing R56 analysis contract: {missing}"

# Default Case Context composition must no longer render the verbose R25 source
# and Qwen glance modules. Historical helper styles may remain for lineage.
case_block = ANALYSIS[ANALYSIS.index('<AnalysisZone index="01"'):ANALYSIS.index('{run && <DownstreamIntelligence')]
assert '<SourceRecord ' not in case_block, 'Old SourceRecord is still rendered in Case Context'
assert '<QwenGlance ' not in case_block, 'Old QwenGlance is still rendered in Case Context'
assert 'understanding.summary' not in case_block, 'Full AI summary leaked into default Case Context composition'
assert 'understanding.keywords' not in case_block, 'Keywords leaked into default Case Context composition'

required_css = [
    'UI-R56 — CASE CONTEXT DISTILLATION',
    '.case-context-workbench-r56',
    'grid-template-columns:minmax(0,1fr) minmax(0,1fr)',
    '.case-source-excerpt-r56',
    '-webkit-line-clamp:3',
    '.qwen-context-fields-r56',
    '.qwen-context-field-r56',
    '.case-context-alert-r56',
    '@container analysis-workbench (max-width:980px)',
    '@container analysis-workbench (max-width:620px)',
    '@container analysis-workbench (max-width:420px)',
]
missing = [token for token in required_css if token not in CSS]
assert not missing, f"Missing R56 CSS contract: {missing}"

# Approved live/runtime/governance behavior must remain wired.
for token in [
    'startAnalysisRun(issue.id)',
    'runIssueUnderstanding(issue.id)',
    'updateIssueUnderstanding(issueId, understanding.id, form)',
    'analysisRunEventsUrl(run.graph_run_id',
    'getRunEvidence(run.graph_run_id)',
    'getImpact(run.graph_run_id)',
    'getRunInvestigations(run.graph_run_id)',
    'getHumanReview(run.graph_run_id)',
    'resumeHumanReview(run.graph_run_id',
    'Priority score, not a defect verdict.',
    'AI finding is advisory.',
    'AI investigates. Humans decide.',
]:
    assert token in ANALYSIS, f"R56 regressed approved Analysis wiring: {token}"

assert 'DISTILL → CLARIFY' in DESIGN
assert 'original `issue.description`' in NOTES
assert 'UI-R57' in NOTES
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
print('UI-R56 verifier: PASS')
print('- Case Context distilled to Human Source vs AI Interpretation')
print('- original ticket and full Qwen proof remain available behind Inspect')
print('- default-visible source is clamped without rewriting source content')
print('- approved Qwen/LangGraph/retrieval/governance wiring preserved')
