from pathlib import Path
root = Path(__file__).resolve().parents[1]
css = (root / 'frontend/app/globals.css').read_text(encoding='utf-8')
tsx = (root / 'frontend/components/analysis-shell.tsx').read_text(encoding='utf-8')
assert 'analysis-r77-rev1' in tsx, 'Missing R77 REV1 Analysis scope class'
checks = [
    'UI-R77 REV1 — EVIDENCE OVERFLOW + READING WIDTH HARDENING',
    '--evidence-source-rail: minmax(300px,.7fr);',
    '--evidence-reading-measure:72ch;',
    'grid-template-columns:24px minmax(0,1fr) 52px;',
    '-webkit-line-clamp:2;',
    'width:52px;',
    'max-width:var(--evidence-reading-measure);',
    'color:color-mix(in oklab,var(--text) 78%,var(--text-soft));',
    '@container analysis-workbench (max-width:960px)',
]
for token in checks:
    assert token in css, f'Missing R77 REV1 CSS contract: {token}'
# Scope guard: this module must not introduce new R78/R79 revisions.
assert 'analysis-r78-rev1' not in tsx
assert 'analysis-r79-rev1' not in tsx
print('UI-R77 REV1 verifier: PASS')
