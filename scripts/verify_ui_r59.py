from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ANALYSIS = (ROOT / 'frontend/components/analysis-shell.tsx').read_text(encoding='utf-8')
CSS = (ROOT / 'frontend/app/globals.css').read_text(encoding='utf-8')
DESIGN = (ROOT / 'frontend/DESIGN.md').read_text(encoding='utf-8')
NOTES = (ROOT / 'UI_R59_NOTES.md').read_text(encoding='utf-8')

required_analysis = [
    'analysis-r59',
    'human-decision-focus-r59',
    'Human review required',
    'ACTION REQUIRED',
    'authority-focus-layout-r59',
    'Priority ${priority}',
    'authority-selected-signals-r59',
    'AI advisory',
    'Choose the governed outcome',
    'authority-choice-r59',
    'selectedDraft?.decision && <label',
    'Why did AI suggest this?',
    'authority-ai-proof-r59',
    'selectedEvidenceRefs.join(" · ")',
    'AI finding is advisory. The human decision is the governed outcome.',
    'Submit decisions',
    'Make the governed decision.',
]
missing = [token for token in required_analysis if token not in ANALYSIS]
assert not missing, f'Missing R59 analysis contract: {missing}'

start = ANALYSIS.index('function HumanDecisionWorkbench({ run, review, learning, decisions, setDecisions, reviewError, busy, onSubmit }: {')
end = ANALYSIS.index('\nfunction DecisionChoice(', start)
block = ANALYSIS[start:end]

# AI prose must be Inspect content, not a permanent default paragraph.
assert 'authority-ai-context-r53' not in block, 'R59 retained the old always-visible AI context panel'
inspect = block.index('<ProgressiveDisclosure label="Why did AI suggest this?"')
statement_pos = block.index('selected.finding?.statement', inspect)
assert statement_pos > inspect, 'Persisted AI statement must be behind progressive disclosure'

# Rationale should appear only after a human choice is made.
assert '{selectedDraft?.decision && <label' in block

# Persisted priority / finding / evidence facts only.
for token in ['selected?.risk_score', 'selected.finding?.type', 'selected.finding?.confidence', 'selectedEvidenceRefs']:
    assert token in block, f'Missing persisted R59 fact: {token}'

# Human final enum and real resume wiring are unchanged.
for token in [
    'value="AFFECTED"',
    'value="NOT_AFFECTED"',
    'value="NEEDS_MORE_INVESTIGATION"',
    'resumeHumanReview(run.graph_run_id',
    'reviewer:"Transformation Assurance Lead"',
    'reason:string',
    'getHumanReview(run.graph_run_id)',
]:
    assert token in ANALYSIS, f'R59 regressed Human Authority wiring: {token}'

required_css = [
    'UI-R59 — Human Decision Focus Mode',
    '.analysis-r59 .human-decision-focus-r59',
    '.authority-focus-head-r59',
    '.authority-focus-layout-r59',
    '.authority-case-r59',
    '.authority-selected-r59',
    '.authority-selected-signals-r59',
    '.authority-decision-r59',
    '.authority-choice-grid-r59',
    '.authority-choice-r59',
    '.authority-ai-proof-r59',
    '.authority-submit-r59',
    '@container analysis-workbench (max-width:900px)',
    '@container analysis-workbench (max-width:700px)',
    '@container analysis-workbench (max-width:520px)',
]
missing = [token for token in required_css if token not in CSS]
assert not missing, f'Missing R59 CSS contract: {missing}'

assert 'CLARIFY → DISTILL' in DESIGN
assert 'Human Authority must visually outrank AI findings' in DESIGN
assert 'UI-R60' in NOTES
assert '3–3000 characters' in NOTES

# Approved no-fake-AI / runtime wiring remains present.
for token in [
    'startAnalysisRun(issue.id)',
    'runIssueUnderstanding(issue.id)',
    'analysisRunEventsUrl(run.graph_run_id',
    'getRunEvidence(run.graph_run_id)',
    'getImpact(run.graph_run_id)',
    'getRunInvestigations(run.graph_run_id)',
    'AI investigates. Humans decide.',
]:
    assert token in ANALYSIS, f'R59 regressed approved Analysis wiring: {token}'

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
print('UI-R59 verifier: PASS')
print('- Human Authority leads the WAITING_HUMAN task surface')
print('- AI prose moved behind Why did AI suggest this?')
print('- decision descriptions are accessible but no longer default-visible')
print('- rationale appears only after a governed decision is selected')
print('- approved Human Review resume and no-fake-AI wiring preserved')
