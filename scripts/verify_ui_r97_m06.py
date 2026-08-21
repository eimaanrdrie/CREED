from pathlib import Path
root=Path(__file__).resolve().parents[1]
analysis=(root/'frontend/components/analysis-shell.tsx').read_text()
css=(root/'frontend/app/globals.css').read_text()
notes=(root/'UI_R97_M06_NOTES.md').read_text()
checks={
 'm05 retained':'human-rationale-r97-m05' in analysis,
 'm06 root marker':'analysis-r97-m06' in analysis,
 'compact receipt':'human-decision-record-summary-r97-m06' in analysis and 'DECISION RECORDED' in analysis,
 'outcome retained':'selected.human_decision.decision.replaceAll' in analysis,
 'authority retained':'selected.human_decision.authority_display_name' in analysis and 'selected.human_decision.authority_role_title' in analysis,
 'rationale preview retained':'selected.human_decision.reason' in analysis,
 'governed disclosure':'label="View governed record"' in analysis,
 'contradiction retained':'DecisionConsistencyWarning consistency={selected.human_decision.decision_consistency as DecisionConsistencyView} recorded' in analysis,
 'm06 CSS':'UI-R97-M06 — Compact Completed Human Decision Record' in css,
 'receipt CSS':'.human-decision-record-summary-r97-m06' in css,
 'governed CSS':'.human-decision-governed-meta-r97-m06' in css,
 'notes baseline':'Builds directly on approved UI-R97-M05' in notes,
 'no invented timestamp':'does not currently expose a decision timestamp' in notes,
}
failed=[k for k,v in checks.items() if not v]
for k,v in checks.items(): print(('PASS' if v else 'FAIL'),k)
if failed: raise SystemExit('UI-R97-M06 verification failed: '+', '.join(failed))
print('UI-R97-M06 verification PASS')
