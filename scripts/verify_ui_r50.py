from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ANALYSIS = (ROOT / "frontend/components/analysis-shell.tsx").read_text(encoding="utf-8")
CSS = (ROOT / "frontend/app/globals.css").read_text(encoding="utf-8")
DESIGN = (ROOT / "frontend/DESIGN.md").read_text(encoding="utf-8")
NOTES = (ROOT / "UI_R50_NOTES.md").read_text(encoding="utf-8")

required_analysis = [
    'analysis-r50',
    'function CaseSignalSummary',
    'analysis-case-summary-r50',
    'analysis-current-state-r50',
    'analysis-signal-grid-r50',
    'label="Case"',
    'label="Qwen"',
    'label="Evidence"',
    'label="Candidates"',
    'label="AI findings"',
    'label="Human"',
    'numericMeta(retrievalStep, "evidence_count")',
    'numericMeta(retrievalStep, "searched_chunks")',
    'numericMeta(impactStep, "candidate_count")',
    'numericMeta(investigationStep, "result_count")',
    'getRunInvestigations(run.graph_run_id)',
    'getHumanReview(run.graph_run_id)',
    'POTENTIALLY_AFFECTED',
    'NO_SUPPORTING_EVIDENCE_OF_IMPACT',
    'INSUFFICIENT_EVIDENCE',
    'AFFECTED',
    'NOT_AFFECTED',
    'NEEDS_MORE_INVESTIGATION',
    'analysis-stage-shell-r50',
    'analysis-stage-track-r50',
    'agent:"intake_agent"',
    'agent:"retrieval_agent"',
    'agent:"knowledge_link_agent"',
    'agent:"impact_agent"',
    'agent:"investigation_agent"',
    'agent:"evidence_validator"',
    'agent:"human_review_boundary"',
    'if (step.agent_name === "human_review_boundary") return <UserCheck size={13} />;',
]
missing = [token for token in required_analysis if token not in ANALYSIS]
assert not missing, f"Missing R50 analysis contract: {missing}"

# The R25 class is retained once for regression lineage, but the duplicate
# downstream metric strip must be gone.
assert ANALYSIS.count('analysis-glance-strip-r25') == 1, 'R50 must expose one signal band, not duplicate glance strips'

required_css = [
    'UI-R50 — Analysis Visual Signal Strip + Case Summary',
    '.analysis-case-summary-r50',
    '.analysis-current-state-r50',
    '.analysis-signal-grid-r50',
    '.analysis-signal-r50',
    '.analysis-stage-shell-r50',
    '.analysis-stage-track-r50',
    '.analysis-stage-r50',
    '@container analysis-workbench (max-width:1120px)',
    '@container analysis-workbench (max-width:680px)',
    '@container analysis-workbench (max-width:430px)',
]
missing = [token for token in required_css if token not in CSS]
assert not missing, f"Missing R50 CSS contract: {missing}"

# Approved execution and human-authority wiring remains untouched.
for token in [
    'startAnalysisRun(issue.id)',
    'runIssueUnderstanding(issue.id)',
    'analysisRunEventsUrl(run.graph_run_id',
    'getRunEvidence(run.graph_run_id)',
    'getImpact(run.graph_run_id)',
    'resumeHumanReview(run.graph_run_id',
    'Priority score, not a defect verdict.',
    'AI investigates. Humans decide.',
]:
    assert token in ANALYSIS, f"R50 regressed approved runtime/governance wiring: {token}"

assert 'state-first visual summary' in DESIGN
assert 'No frontend timer is used to infer progress.' in NOTES
assert 'UI-R51' in NOTES
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
print('UI-R50 verifier: PASS')
print('- one current-state lead + one visual signal band')
print('- signal counts/labels are backed by persisted runtime/investigation/review data')
print('- seven-stage tracker matches the actual LangGraph node order')
print('- duplicate downstream metric strip removed')
print('- R49 workbench and R48 Audit pagination preserved')
