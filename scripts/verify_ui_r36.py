from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
css = (ROOT/'frontend/app/globals.css').read_text(encoding='utf-8')
ts = (ROOT/'frontend/components/ai-runtime-console.tsx').read_text(encoding='utf-8')
required_css = [
    'UI-R36 — Execution Proof component-width containment',
    'container-type:inline-size',
    '.runtime-execution-meta-r36',
    '@container (max-width:900px)',
    '@container (max-width:560px)',
]
required_ts = [
    'className="runtime-execution-meta-r36"',
    '<time dateTime={execution.completed_at ?? undefined}>{formatTime(execution.completed_at)}</time>',
]
missing=[x for x in required_css if x not in css] + [x for x in required_ts if x not in ts]
if missing:
    raise SystemExit('UI-R36 verification failed; missing: '+', '.join(missing))
# crude balanced-brace checks
for name, text in [('CSS', css), ('TSX', ts)]:
    if text.count('{') != text.count('}'):
        raise SystemExit(f'{name} brace imbalance')
print('UI-R36 verification: PASS')
