from pathlib import Path
root=Path(__file__).resolve().parents[1]
ts=(root/'frontend/components/analysis-shell.tsx').read_text()
css=(root/'frontend/app/globals.css').read_text()
checks={
 'root class':'analysis-r98-m06' in ts,
 'stage helper':'function LearningStageRow' in ts,
 'stage list':'learning-stage-list-r98-m06' in ts,
 'proposal stage':'title="Learning proposal"' in ts,
 'authority stage':'title="Learning authority"' in ts,
 'receipt stage':'title="Adoption receipt"' in ts,
 'single open state':'setOpenStage' in ts and 'openStage === "authority"' in ts,
 'human correction preserved':'HUMAN CORRECTION' in ts and 'Generate learning proposal' in ts,
 'learning decision preserved':'decide("APPROVE_LEARNING")' in ts and 'decide("REJECT_LEARNING")' in ts,
 'scope preserved':'ADOPTION SCOPE' in ts and 'SELECTED_IMPLEMENTATIONS' in ts,
 'receipt verification preserved':'verifyReceipt()' in ts and 'SHA-256 verification passed' in ts,
 'accordion css':'.learning-stage-list-r98-m06' in css and '.learning-stage-trigger-r98-m06' in css,
}
failed=[]
for name,ok in checks.items():
    print(('PASS' if ok else 'FAIL'),name)
    if not ok: failed.append(name)
if failed: raise SystemExit('UI-R98-M06 verification FAILED: '+', '.join(failed))
print('UI-R98-M06 verification PASS')
