from pathlib import Path
root = Path(__file__).resolve().parents[1]
css = (root / 'frontend/app/globals.css').read_text()
tsx = (root / 'frontend/components/analysis-shell.tsx').read_text()
assert 'analysis-r76-rev1 analysis-r76-rev2' in tsx
checks = [
    'UI-R76 REV2 — CASE CONTEXT OUTER INSET + PROOF VALUE CONTRAST',
    '--context-outer-inset-x:12px;',
    '.analysis-r76-rev2 .analysis-zone-r49:first-of-type .analysis-zone-body-r49 {',
    'padding:0 var(--context-outer-inset-x) var(--context-outer-inset-bottom);',
    '.analysis-r76-rev2 .understanding-r04 .ai-field-r04.unknown > strong {',
    '.analysis-r76-rev2 .case-source-proof-grid-r56 .source-cell-r04 > strong.code {',
    '.analysis-r76-rev2 .understanding-r04 .model-proof-r04 span {',
]
for c in checks:
    assert c in css, c
# Guard semantics: unknown/unverified is deliberately neutral, not amber/red.
segment = css.split('UI-R76 REV2 — CASE CONTEXT OUTER INSET + PROOF VALUE CONTRAST',1)[1]
unknown = segment.split('.analysis-r76-rev2 .understanding-r04 .ai-field-r04.unknown > strong {',1)[1].split('}',1)[0]
assert 'var(--amber)' not in unknown and 'var(--red)' not in unknown
print('UI-R76 REV2 verifier: PASS')
