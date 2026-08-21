from pathlib import Path
root=Path(__file__).resolve().parents[1]
ts=(root/'frontend/components/analysis-shell.tsx').read_text()
css=(root/'frontend/app/globals.css').read_text()
checks={
 'root class':'analysis-r98-m05' in ts,
 'evidence zone class':'analysis-zone-evidence-r98-m05' in ts,
 'handoff zone class':'analysis-zone-handoff-r98-m05' in ts,
 'zone class prop':'className?:string' in ts and 'analysis-zone-r49 ${className}' in ts,
 'minimal learning class':'learning-minimal-r98-m05' in ts,
 'proposal summary':'learning-proposal-summary-r98-m05' in ts,
 'redundant governed head removed':'<div className="governed-learning-head-r53">' not in ts,
 'evidence single-boundary css':'.analysis-zone-evidence-r98-m05 .analysis-zone-body-r49' in css and 'border:0;' in css,
 'minimal handoff css':'.learning-minimal-r98-m05' in css,
 'compact scope css':'.learning-scope-modes-r94-m08 small { display:none; }' in css,
 'active governance preserved':'decide("APPROVE_LEARNING")' in ts and 'decide("REJECT_LEARNING")' in ts,
 'original source flow preserved':'SourceEvidenceModal' in ts and 'openSelectedSource' in ts,
}
failed=[]
for name,ok in checks.items():
    print(('PASS' if ok else 'FAIL'),name)
    if not ok: failed.append(name)
if failed: raise SystemExit('UI-R98-M05 verification FAILED: '+', '.join(failed))
print('UI-R98-M05 verification PASS')
