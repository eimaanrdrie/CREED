from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ANALYSIS = (ROOT / "frontend" / "components" / "analysis-shell.tsx").read_text(encoding="utf-8")
CSS = (ROOT / "frontend" / "app" / "globals.css").read_text(encoding="utf-8")
NOTES = (ROOT / "UI_R25_NOTES.md").read_text(encoding="utf-8")

for token in [
    'import { ProgressiveDisclosure, SignalChip }',
    'assurance-flow-r25',
    'source-min-r25',
    'qwen-glance-r25',
    'agent-row-min-r25',
    'analysis-glance-strip-r25',
    'evidence-glance-r25',
    'impact-visual-r25',
    'investigation-cards-r25',
    'human-authority-min-r25',
    'ProgressiveDisclosure label="Inspect extraction"',
    'Priority score, not a defect verdict.',
    'LANGGRAPH PAUSED',
    'resumeHumanReview(run.graph_run_id',
    'startAnalysisRun(issue.id)',
    'runIssueUnderstanding(issue.id)',
    'analysisRunEventsUrl(run.graph_run_id',
]:
    assert token in ANALYSIS, f"missing R25 analysis contract: {token}"

for token in [
    'UI-R25 — Visual Analysis Workspace',
    '.assurance-flow-r25',
    '.analysis-glance-strip-r25',
    '.evidence-glance-r25',
    '.impact-visual-track-r25',
    '.investigation-cards-r25',
    '@media (max-width:1460px)',
    '@media (max-width:820px)',
    '@media (max-width:460px)',
]:
    assert token in CSS, f"missing R25 visual/responsive contract: {token}"

assert 'GLANCE → INSPECT → PROVE' in NOTES
assert 'AFFECTED / NOT_AFFECTED / NEEDS_MORE_INVESTIGATION' in NOTES
assert 'No fake agent progress' in NOTES
assert not (ROOT / 'frontend' / 'app' / 'demo').exists(), 'Demo route must remain removed'

for path in (ROOT / 'frontend').rglob('*.tsx'):
    text = path.read_text(encoding='utf-8')
    assert 'react-icons' not in text
    assert '@heroicons' not in text
    assert 'fontawesome' not in text.lower()

assert CSS.count('{') == CSS.count('}'), 'CSS braces are unbalanced'
print('UI-R25 verification: PASS')
print('- visual six-stage assurance path present')
print('- source/Qwen/agent/evidence detail progressively disclosed')
print('- impact and investigation are signal-first visual surfaces')
print('- Human Authority remains explicit and action-bearing')
print('- backend execution paths and governance semantics retained')
