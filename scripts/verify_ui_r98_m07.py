from pathlib import Path
root=Path(__file__).resolve().parents[1]
knowledge=(root/'frontend/components/knowledge-workspace.tsx').read_text()
sidebar=(root/'frontend/components/sidebar.tsx').read_text()
css=(root/'frontend/app/globals.css').read_text()
checks={
 'knowledge root class':'knowledge-find-r98-m07' in knowledge,
 'visible document list':'Knowledge documents' in knowledge and 'knowledge-library-list-r98-m07' in knowledge,
 'repository filters':'knowledge-library-filters-r98-m07' in knowledge and 'registryQuery' in knowledge,
 'document inspect preserved':'openDocument(doc.id)' in knowledge and 'setMode("inspect")' in knowledge,
 'hybrid retrieval preserved':'Search evidence' in knowledge and 'runSearch' in knowledge and 'searchKnowledge' in knowledge,
 'hidden evidence registry removed':'label="Evidence registry"' not in knowledge,
 'provenance disclosure preserved':'label="Provenance & ranking"' in knowledge,
 'change radar removed from core nav':'{ label: "Change Radar"' not in sidebar,
 'change radar route not deleted':(root/'frontend/app/change-radar/page.tsx').exists(),
 'list css':'.knowledge-library-r98-m07' in css and '.knowledge-library-row-r98-m07' in css,
}
failed=[]
for name,ok in checks.items():
    print(('PASS' if ok else 'FAIL'),name)
    if not ok: failed.append(name)
if failed: raise SystemExit('UI-R98-M07 verification FAILED: '+', '.join(failed))
print('UI-R98-M07 verification PASS')
