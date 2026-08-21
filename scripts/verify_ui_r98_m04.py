from pathlib import Path
root=Path(__file__).resolve().parents[1]
analysis=(root/'frontend/components/analysis-shell.tsx').read_text()
css=(root/'frontend/app/globals.css').read_text()
notes=(root/'UI_R98_M04_NOTES.md').read_text()
checks={
 'lineage':'Builds directly on approved UI-R98-M03' in notes,
 'root class':'analysis-r98-m04' in analysis,
 'guard condition':'!handoffAttention' in analysis and 'beforeunload' in analysis,
 'internal anchor interception':'document.addEventListener("click", onDocumentClick, true)' in analysis,
 'same issue workspace allowed':'destination.pathname === current.pathname' in analysis,
 'modal copy':'Learning & Adoption is incomplete' in analysis,
 'continue action':'Continue workflow' in analysis and 'selectWorkspace("handoff")' in analysis,
 'leave anyway':'Leave anyway' in analysis and 'window.location.assign(pendingNavigationHref)' in analysis,
 'bypass prevents loop':'navigationGuardBypassRef.current = true' in analysis,
 'terminal rejected':'proposal?.status === "REJECTED"' in analysis,
 'terminal receipt':'proposal?.status === "APPROVED" && Boolean(proposal.adoption_receipt)' in analysis,
 'completion state':'handoffComplete' in analysis and 'workflow-complete-r98-m04' in analysis,
 'completion icon':'workflow-complete-icon-r98-m04' in analysis,
 'guard css':'handoff-leave-layer-r98-m04' in css and 'handoff-leave-dialog-r98-m04' in css,
 'responsive dialog':'@media (max-width:560px)' in css,
 'no hard lock':'No route is hard-locked.' in notes,
 'semantics unchanged':'No Human Decision, Qwen, LangGraph' in notes,
}
failed=[k for k,v in checks.items() if not v]
for k,v in checks.items(): print(('PASS' if v else 'FAIL'),k)
if failed: raise SystemExit('UI-R98-M04 verification failed: '+', '.join(failed))
print('UI-R98-M04 verification PASS')
