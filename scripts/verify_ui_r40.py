from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
css = (ROOT / 'frontend/app/globals.css').read_text(encoding='utf-8')
required = [
    'UI-R40 — Knowledge panel alignment + border normalization',
    '.knowledge-search-stage-r27,\n.knowledge-proof-stack-r27',
    'inline-size:100%',
    'border:1px solid var(--line)',
    '.knowledge-proof-stack-r27 > .progressive-disclosure[open] > summary',
    'padding:16px 18px 18px',
]
missing = [item for item in required if item not in css]
if missing:
    raise SystemExit('UI-R40 verification failed: missing ' + ', '.join(missing))
print('UI-R40 verification: PASS')
