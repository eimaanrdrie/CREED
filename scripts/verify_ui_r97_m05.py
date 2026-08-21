from pathlib import Path
root=Path(__file__).resolve().parents[1]
analysis=(root/'frontend/components/analysis-shell.tsx').read_text()
css=(root/'frontend/app/globals.css').read_text()
notes=(root/'UI_R97_M05_NOTES.md').read_text()
checks={
 'm04 retained':'human-decision-card-head-r97-m04' in analysis,
 'm05 root marker':'analysis-r97-m05' in analysis,
 'rationale mode':'selectedRationaleMode' in analysis,
 'aligned compact rows':'rows={selectedRationaleMode === "aligned" ? 1 : 3}' in analysis,
 'needs-more mode':'selectedDraft?.decision === "NEEDS_MORE_INVESTIGATION"' in analysis,
 'exception preserved':'selectedConsistency?.contradiction' in analysis and 'R9406_CONTRADICTION_RATIONALE_MIN_CHARS' in analysis,
 'mandatory rationale preserved':'Choose a decision and rationale for every implementation.' in analysis,
 '3000 max preserved':'maxLength={3000}' in analysis,
 'atomic submit preserved':'Submit decisions' in analysis,
 'm05 CSS':'UI-R97-M05 — Smart / Minimal Human Decision Rationale' in css,
 'aligned CSS':'.human-rationale-r97-m05.mode-aligned textarea' in css,
 'expanded CSS':'.human-rationale-r97-m05.mode-investigation textarea' in css and '.human-rationale-r97-m05.mode-exception textarea' in css,
 'notes baseline':'Builds directly on approved UI-R97-M04' in notes,
}
failed=[k for k,v in checks.items() if not v]
for k,v in checks.items(): print(('PASS' if v else 'FAIL'),k)
if failed: raise SystemExit('UI-R97-M05 verification failed: '+', '.join(failed))
print('UI-R97-M05 verification PASS')
