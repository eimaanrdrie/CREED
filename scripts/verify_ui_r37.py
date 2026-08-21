from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
css=(ROOT/'frontend/app/globals.css').read_text(encoding='utf-8')
ts=(ROOT/'frontend/components/knowledge-workspace.tsx').read_text(encoding='utf-8')
required_css=[
    'UI-R37 — Knowledge proof-stack component-width containment',
    'container:knowledge-proof / inline-size',
    '@container knowledge-proof (max-width:860px)',
    '@container knowledge-proof (max-width:720px)',
    '@container knowledge-proof (max-width:520px)',
    '.registry-min-r27 .registry-row-r06 [data-label]::before',
    '.knowledge-provenance-min-r27 > div > span',
]
required_ts=[
    'ProgressiveDisclosure label="Evidence registry"',
    'ProgressiveDisclosure label="Provenance & ranking"',
    'className="knowledge-proof-stack-r27"',
]
missing=[x for x in required_css if x not in css]+[x for x in required_ts if x not in ts]
if missing:
    raise SystemExit('UI-R37 verification failed; missing: '+', '.join(missing))
for name,text in [('CSS',css),('TSX',ts)]:
    if text.count('{')!=text.count('}'):
        raise SystemExit(f'{name} brace imbalance')
print('UI-R37 verification: PASS')
