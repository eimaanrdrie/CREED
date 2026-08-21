from pathlib import Path
root = Path(__file__).resolve().parents[1]
css = (root / 'frontend/app/globals.css').read_text(encoding='utf-8')
tsx = (root / 'frontend/components/analysis-shell.tsx').read_text(encoding='utf-8')
assert 'analysis-r78-rev1' in tsx, 'Missing R78 REV1 scope class'
for token in [
    'UI-R78 REV1 — INVESTIGATION AI-SIGNAL + SEMANTIC COLOR CLEANUP',
    '.analysis-r78-rev1 .investigation-focus-head-r58 > svg',
    'background:color-mix(in oklab,var(--creed-warning) 78%,var(--creed-secondary));',
    '.analysis-r78-rev1 .investigation-ai-clamp-r58,',
    '.analysis-r78-rev1 .investigation-matrix-row-r58.selected',
]:
    assert token in css, f'Missing R78 REV1 CSS contract: {token}'
block = tsx[tsx.index('function findingTone'):tsx.index('function RunState')]
assert 'if (value === "POTENTIALLY_AFFECTED") return "warn";' in block
assert 'if (value === "INSUFFICIENT_EVIDENCE") return "warn";' in block
assert 'if (value === "NO_SUPPORTING_EVIDENCE_OF_IMPACT") return "neutral";' in block
assert 'return "info"' not in block, 'AI findings must not use generic info/cyan tone'
# Preserve approved semantics and runtime wiring.
assert 'Priority ≠ verdict' in tsx
for token in ['getImpact(run.graph_run_id)', 'getRunInvestigations(run.graph_run_id)', 'resumeHumanReview(run.graph_run_id']:
    assert token in tsx, f'Runtime wiring regressed: {token}'
assert 'analysis-r79-rev1' not in tsx, 'R79 REV1 must not be started'
print('UI-R78 REV1 verifier: PASS')
