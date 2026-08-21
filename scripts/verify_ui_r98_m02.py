from pathlib import Path
root=Path(__file__).resolve().parents[1]
analysis=(root/'frontend/components/analysis-shell.tsx').read_text()
css=(root/'frontend/app/globals.css').read_text()
notes=(root/'UI_R98_M02_NOTES.md').read_text()
checks={
 'lineage':'Builds directly on approved UI-R98-M01' in notes,
 'root class':'analysis-r98-m02' in analysis,
 'tab renamed':'label:"Learning & Adoption"' in analysis,
 'old tab label removed':'label:"Governed Handoff"' not in analysis,
 'workspace id preserved':'id:"handoff"' in analysis and 'type AnalysisWorkspace = "context" | "evidence" | "investigation" | "human" | "handoff"' in analysis,
 'zone renamed':'title="Learning & Adoption"' in analysis,
 'pending renamed':'Learning & Adoption not available yet' in analysis,
 'real wait signal':'const needsHuman = run?.status === "WAITING_HUMAN";' in analysis,
 'attention dot preserved':'analysis-workspace-action-r62' in analysis,
 'pulse css':'r98HumanDecisionDot' in css and 'r98HumanDecisionBadge' in css,
 'reduced motion':'prefers-reduced-motion: reduce' in css,
 'no auto navigation claim':'No auto-navigation is added in this module.' in notes,
 'semantics unchanged':'No change to Human Decision semantics' in notes,
}
failed=[k for k,v in checks.items() if not v]
for k,v in checks.items(): print(('PASS' if v else 'FAIL'),k)
if failed: raise SystemExit('UI-R98-M02 verification failed: '+', '.join(failed))
print('UI-R98-M02 verification PASS')
