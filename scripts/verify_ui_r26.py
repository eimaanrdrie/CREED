from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RADAR = (ROOT / "frontend" / "components" / "change-radar-workspace.tsx").read_text(encoding="utf-8")
CSS = (ROOT / "frontend" / "app" / "globals.css").read_text(encoding="utf-8")
NOTES = (ROOT / "UI_R26_NOTES.md").read_text(encoding="utf-8")

for token in [
    'import { ProgressiveDisclosure, SignalChip, VisualMetric }',
    'radar-glance-r26',
    'radar-stage-r26',
    'radar-flow-canvas-r26',
    'radar-selection-r26',
    'radar-selection-grid-r26',
    'radar-signal-track-r26',
    'ProgressiveDisclosure label="Inspect evidence"',
    'label={mode === "impact" ? "Implementation list" : "Routed adopters"}',
    'ProgressiveDisclosure label="Dependency proof"',
    'Priority ≠ verdict',
    'Route = review obligation',
    'getImpact(run)',
    'getRecall(recall)',
    'setEvidenceDetail(await getDocument(id))',
    'USES_METHOD_VERSION dependency',
]:
    assert token in RADAR, f"missing R26 radar contract: {token}"

assert 'radar-inspector-r05' not in RADAR, 'R26 must not keep the permanent side inspector'
assert 'radar-summary-strip' not in RADAR, 'R26 must not keep the old explanatory summary strip'
assert 'radar-toolbar' not in RADAR, 'R26 filters belong in the graph command header'

for token in [
    'UI-R26 — Visual Change Radar',
    '.radar-glance-r26',
    '.radar-stage-r26',
    '.radar-flow-canvas-r26',
    '.radar-selection-grid-r26',
    '.radar-signal-track-r26',
    '.radar-ledger-min-r26',
    '@media (max-width:820px)',
    '@media (max-width:460px)',
]:
    assert token in CSS, f"missing R26 visual/responsive contract: {token}"

assert 'GLANCE → SELECT → PROVE' in NOTES
assert 'Impact score remains investigation priority, not a defect verdict.' in NOTES
assert 'No fake AI' in NOTES
assert not (ROOT / 'frontend' / 'app' / 'demo').exists(), 'Demo route must remain removed'

for path in (ROOT / 'frontend').rglob('*.tsx'):
    text = path.read_text(encoding='utf-8')
    assert 'react-icons' not in text
    assert '@heroicons' not in text
    assert 'fontawesome' not in text.lower()

assert CSS.count('{') == CSS.count('}'), 'CSS braces are unbalanced'
print('UI-R26 verification: PASS')
print('- Change Radar is graph-first with no permanent side inspector')
print('- candidate/recall detail appears only after node selection')
print('- deterministic signal bars and evidence proof remain inspectable')
print('- implementation ledger and legend use progressive disclosure')
print('- impact/recall governance semantics and backend data paths retained')
