from pathlib import Path
root=Path(__file__).resolve().parents[1]
analysis=(root/'frontend/components/analysis-shell.tsx').read_text()
css=(root/'frontend/app/globals.css').read_text()
notes=(root/'UI_R98_M03_NOTES.md').read_text()
checks={
 'lineage':'Builds directly on approved UI-R98-M02' in notes,
 'root class':'analysis-r98-m03' in analysis,
 'auto next callback':'onHumanReviewComplete' in analysis and 'selectWorkspace("handoff")' in analysis,
 'only after persisted complete':'if (latest.status === "COMPLETED") onHumanReviewComplete(latest);' in analysis,
 'arrival notice':'Human decisions recorded' in analysis and 'handoff-arrival-r98-m03' in analysis,
 'handoff action prop':'handoffAction={handoffAttention}' in analysis,
 'readiness driven':'getLearningReadiness(run.graph_run_id)' in analysis,
 'terminal attention boundary':'proposal?.status === "REJECTED"' in analysis and 'proposal?.status === "APPROVED" && Boolean(proposal.adoption_receipt)' in analysis,
 'handoff class':'handoff-action-required' in analysis,
 'attention css':'r98HandoffTabPulse' in css and 'r98HandoffDotPulse' in css,
 'reduced motion':'prefers-reduced-motion: reduce' in css,
 'stage correction':'Human correction required' in analysis,
 'stage approval':'Learning approval required' in analysis,
 'stage receipt':'Adoption receipt pending' in analysis,
 'stage complete':'Learning & Adoption complete' in analysis,
 'm04 deferred':'No navigation-leave warning is included yet; that is UI-R98-M04.' in notes,
 'semantics unchanged':'No change to Human Decision semantics' in notes,
}
failed=[k for k,v in checks.items() if not v]
for k,v in checks.items(): print(('PASS' if v else 'FAIL'),k)
if failed: raise SystemExit('UI-R98-M03 verification failed: '+', '.join(failed))
print('UI-R98-M03 verification PASS')
