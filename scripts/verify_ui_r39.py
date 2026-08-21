from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
css=(ROOT/'frontend/app/globals.css').read_text(encoding='utf-8')
required=[
 'UI-R39 — Knowledge Proof hard-containment follow-up',
 'inline-size:min(100%,1180px)',
 'repeat(auto-fit,minmax(min(100%,250px),1fr))',
 '@container knowledge-proof (max-width:980px)',
 '.registry-min-r27 .registry-search-r06',
]
missing=[x for x in required if x not in css]
if missing:
    raise SystemExit('UI-R39 verification failed: missing '+', '.join(missing))
print('UI-R39 verification: PASS')
