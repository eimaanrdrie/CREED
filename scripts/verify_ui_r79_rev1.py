from pathlib import Path
root=Path(__file__).resolve().parents[1]
tsx=(root/'frontend/components/analysis-shell.tsx').read_text(encoding='utf-8')
css=(root/'frontend/app/globals.css').read_text(encoding='utf-8')
checks=[
    ('scope','analysis-r79-rev1' in tsx),
    ('progress transform inline','transform:`scaleX(${items.length ? Math.min(1, Math.max(0, readyCount / items.length)) : 0})`' in tsx),
    ('no progress width inline','<i style={{ width:`${items.length ? Math.round((readyCount / items.length) * 100) : 0}%` }} />' not in tsx),
    ('module css','UI-R79 REV1 — HUMAN DECISION MOTION + AUTHORITY HIERARCHY' in css),
    ('full width progress bar','.analysis-r79-rev1 .authority-review-track-r67 > i' in css and 'width:100%;' in css),
    ('transform transition','transition:transform .16s ease;' in css),
    ('neutral unselected choice','.analysis-r79-rev1 .authority-choice-r67 .authority-choice-icon-r53' in css),
    ('affected selected semantic','[data-decision="AFFECTED"].selected' in css),
    ('not affected selected semantic','[data-decision="NOT_AFFECTED"].selected' in css),
    ('needs investigation selected semantic','[data-decision="NEEDS_MORE_INVESTIGATION"].selected' in css),
]
failed=[name for name,ok in checks if not ok]
if failed:
    raise SystemExit('UI-R79 REV1 verifier failed: '+', '.join(failed))
print('UI-R79 REV1 verifier: PASS')
