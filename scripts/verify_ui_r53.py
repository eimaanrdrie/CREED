from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ANALYSIS = (ROOT / "frontend/components/analysis-shell.tsx").read_text(encoding="utf-8")
CSS = (ROOT / "frontend/app/globals.css").read_text(encoding="utf-8")
DESIGN = (ROOT / "frontend/DESIGN.md").read_text(encoding="utf-8")
NOTES = (ROOT / "UI_R53_NOTES.md").read_text(encoding="utf-8")

required_analysis = [
    'analysis-r53',
    'function HumanDecisionWorkbench',
    'human-decision-workbench-r53',
    'authority-command-r53',
    'authority-boundary-r53',
    'AI finding is advisory.',
    'authority-layout-r53',
    'authority-master-r53',
    'authority-case-r53',
    'aria-pressed={active}',
    'setSelectedReviewId(item.id)',
    'authority-detail-r53',
    'authority-ai-context-r53',
    'authority-choice-grid-r53',
    'DecisionChoice value="AFFECTED"',
    'DecisionChoice value="NOT_AFFECTED"',
    'DecisionChoice value="NEEDS_MORE_INVESTIGATION"',
    'authority-rationale-input-r53',
    'maxLength={3000}',
    'authority-submit-r53',
    'Ready to resume LangGraph',
    'Submit all decisions',
    'function GovernedLearningHandoff',
    'A learning proposal is not approved reusable knowledge until the separate human learning-approval step records that authority.',
    'selected.human_decision.reviewer',
    'selected.human_decision.reason',
]
missing = [token for token in required_analysis if token not in ANALYSIS]
assert not missing, f"Missing R53 analysis contract: {missing}"

# Old repeated decision-card rendering is replaced by the authority workbench.
assert 'className="card human-authority-r04 human-authority-min-r25"' not in ANALYSIS
assert 'className="review-ledger-r04"' not in ANALYSIS
assert 'className="decision-grid-r04"' not in ANALYSIS
assert 'className="card learning-handoff-r04 analysis-min-module-r25"' not in ANALYSIS

required_css = [
    'UI-R53 — Analysis Human Authority + Decision Workbench',
    '.analysis-r53 .human-decision-workbench-r53',
    '.authority-command-r53',
    '.authority-boundary-r53',
    '.authority-layout-r53',
    '.authority-master-r53',
    '.authority-case-r53.selected',
    '.authority-detail-r53',
    '.authority-ai-context-r53',
    '.authority-choice-grid-r53',
    '.authority-choice-r53.selected',
    '.authority-rationale-input-r53',
    '.authority-submit-r53',
    '.governed-learning-r53',
    '@container analysis-workbench (max-width:880px)',
    '@container analysis-workbench (max-width:680px)',
    '@container analysis-workbench (max-width:440px)',
]
missing = [token for token in required_css if token not in CSS]
assert not missing, f"Missing R53 CSS contract: {missing}"

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
    'reviewer:"Transformation Assurance Lead"',
    'Priority score, not a defect verdict.',
    'AI investigates. Humans decide.',
    '"AFFECTED"',
    '"NOT_AFFECTED"',
    '"NEEDS_MORE_INVESTIGATION"',
    'LANGGRAPH PAUSED',
]:
    assert token in ANALYSIS, f"R53 regressed approved analysis wiring: {token}"

assert 'Operate-mode authority workbench' in DESIGN
assert 'No backend file, API contract, database model or LangGraph graph changed.' in NOTES
assert 'UI-R54' in NOTES
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
print('UI-R53 verifier: PASS')
print('- Human Authority is one master/detail decision workbench')
print('- AI finding remains advisory; persisted human outcome is visually primary')
print('- complete-review submission still uses the approved LangGraph resume path')
print('- governed learning remains downstream and separately approval-gated')
print('- R52/R51/R50/R49/R48 continuity preserved')
