from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ANALYSIS = (ROOT / 'frontend/components/analysis-shell.tsx').read_text(encoding='utf-8')
CSS = (ROOT / 'frontend/app/globals.css').read_text(encoding='utf-8')
DESIGN = (ROOT / 'frontend/DESIGN.md').read_text(encoding='utf-8')
NOTES = (ROOT / 'UI_R67_NOTES.md').read_text(encoding='utf-8')

for token in [
    'analysis-r67',
    'GOVERNED REVIEW',
    'authority-focus-meta-r59 authority-focus-meta-r67',
    'authority-review-progress-r67',
    'role="progressbar"',
    'aria-valuenow={readyCount}',
    'REVIEW QUEUE',
    'authority-case-r53 authority-case-r59 authority-case-r67',
    'DECISION TASK',
    'STEP 1',
    'Choose human outcome',
    'data-decision={value}',
    'STEP 2',
    'Decision rationale',
    'ProgressiveDisclosure label="Why did AI suggest this?"',
    'authority-ai-boundary-r59 sr-only',
    'STEP 3',
    'Submit human decisions',
    'Submit decisions',
    'items.length - readyCount',
]:
    assert token in ANALYSIS, f'Missing R67 Analysis contract: {token}'

start = ANALYSIS.index('function HumanDecisionWorkbench(')
end = ANALYSIS.index('\nfunction DecisionChoice(', start)
block = ANALYSIS[start:end]

# Human action stays primary; model statement remains inspect-only.
inspect = block.index('<ProgressiveDisclosure label="Why did AI suggest this?"')
assert block.index('selected.finding?.statement', inspect) > inspect
assert '{selectedDraft?.decision && <label' in block
assert '<ArrowRight size={14} aria-hidden="true" />' not in block, 'Decorative review-row arrow remains in R67'

# Existing Human Authority semantics and actual resume wiring are unchanged.
for token in [
    'value="AFFECTED"',
    'value="NOT_AFFECTED"',
    'value="NEEDS_MORE_INVESTIGATION"',
    'resumeHumanReview(run.graph_run_id',
    'reviewer:"Transformation Assurance Lead"',
    'reason:string',
    'getHumanReview(run.graph_run_id)',
    '(decisions[item.id]?.reason?.trim().length ?? 0) >= 3',
]:
    assert token in ANALYSIS, f'R67 regressed Human Authority wiring: {token}'

for token in [
    'UI-R67 — Human Decision Task Flow refinement',
    '.analysis-r67 .human-decision-focus-r59',
    '.authority-review-progress-r67',
    '.authority-review-track-r67',
    '.analysis-r67 .authority-case-r67',
    '.analysis-r67 .authority-selected-r67',
    '.analysis-r67 .authority-choice-r67',
    '[data-decision="AFFECTED"]',
    '[data-decision="NOT_AFFECTED"]',
    '[data-decision="NEEDS_MORE_INVESTIGATION"]',
    '.analysis-r67 .authority-rationale-input-r67',
    '.analysis-r67 .authority-submit-r67',
    '@container analysis-workbench (max-width:900px)',
    '@container analysis-workbench (max-width:700px)',
    '@container analysis-workbench (max-width:520px)',
]:
    assert token in CSS, f'Missing R67 CSS contract: {token}'

for token in [
    'startAnalysisRun(issue.id)',
    'runIssueUnderstanding(issue.id)',
    'analysisRunEventsUrl(run.graph_run_id',
    'getRunEvidence(run.graph_run_id)',
    'getImpact(run.graph_run_id)',
    'getRunInvestigations(run.graph_run_id)',
    'getHumanReview(run.graph_run_id)',
    'Agent Execution Task',
]:
    assert token in ANALYSIS, f'R67 regressed approved runtime wiring: {token}'

assert 'Human Decision task flow refinement' in DESIGN
assert 'No backend source file was changed' in NOTES
assert 'UI-R68' in NOTES
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
print('UI-R67 verifier: PASS')
print('- Human Decision is a short governed task sequence')
print('- review progress is derived from real review completeness')
print('- AI finding remains inspect-only and advisory')
print('- approved Human Review resume/governance wiring preserved')
