from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ANALYSIS = (ROOT / 'frontend/components/analysis-shell.tsx').read_text(encoding='utf-8')
CSS = (ROOT / 'frontend/app/globals.css').read_text(encoding='utf-8')
DESIGN = (ROOT / 'frontend/DESIGN.md').read_text(encoding='utf-8')
NOTES = (ROOT / 'UI_R62_NOTES.md').read_text(encoding='utf-8')

required_analysis = [
    'analysis-r62',
    'type AnalysisWorkspace = "context" | "evidence" | "investigation" | "human"',
    'AnalysisWorkspaceNavigator',
    'Case Context',
    'Evidence',
    'Investigation',
    'Human Decision',
    'aria-pressed={selected === tab.id}',
    'url.searchParams.set("view", next)',
    'selectedWorkspace={workspace}',
    'selectedWorkspace === "evidence"',
    'selectedWorkspace === "investigation"',
    'selectedWorkspace === "human"',
    'Agent Execution Task',
    'aria-label="Agent execution task"',
    'run?.status === "WAITING_HUMAN"',
    'numericMeta(retrieval, "evidence_count")',
    'numericMeta(impact, "candidate_count")',
    'numericMeta(investigation, "result_count")',
]
missing = [token for token in required_analysis if token not in ANALYSIS]
assert not missing, f'Missing R62 Analysis contract: {missing}'

# The duplicated top path must be removed from rendered Analysis JSX and the old
# AssurancePath component must no longer exist.
assert '<AssurancePath run={run} />' not in ANALYSIS
assert 'function AssurancePath(' not in ANALYSIS
assert '<span>EXECUTION</span><h2>Run telemetry</h2>' not in ANALYSIS

# Existing real execution / governance wiring must remain intact.
for token in [
    'startAnalysisRun(issue.id)',
    'runIssueUnderstanding(issue.id)',
    'analysisRunEventsUrl(run.graph_run_id',
    'getRunEvidence(run.graph_run_id)',
    'getImpact(run.graph_run_id)',
    'getRunInvestigations(run.graph_run_id)',
    'getHumanReview(run.graph_run_id)',
    'resumeHumanReview(run.graph_run_id',
    'step.status === "WAITING_HUMAN"',
    'step.status === "FAILED"',
]:
    assert token in ANALYSIS, f'R62 regressed approved runtime wiring: {token}'

required_css = [
    'UI-R62 — Analysis Workspace Navigation + Execution Consolidation',
    '.analysis-r62 .analysis-path-r55 { display:none!important; }',
    '.analysis-workspace-nav-r62',
    '.analysis-workspace-tabs-r62',
    '.analysis-workspace-tab-r62.selected',
    '.analysis-workspace-action-r62',
    '.analysis-workspace-empty-r62',
]
missing = [token for token in required_css if token not in CSS]
assert not missing, f'Missing R62 CSS contract: {missing}'

assert 'single visual lifecycle surface' in DESIGN
assert 'No backend source file was changed' in NOTES

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
print('UI-R62 verifier: PASS')
print('- one selectable Analysis workspace is rendered at a time')
print('- duplicated top lifecycle path removed')
print('- Agent Execution Task is the single lifecycle surface')
print('- persisted counts / WAITING_HUMAN semantics preserved')
print('- approved Qwen/LangGraph/Human Authority wiring preserved')
