from pathlib import Path
root=Path(__file__).resolve().parents[1]
analysis=(root/'frontend/components/analysis-shell.tsx').read_text()
css=(root/'frontend/app/globals.css').read_text()
notes=(root/'UI_R97_M08_NOTES.md').read_text()

human=analysis[analysis.index('function HumanDecisionWorkbench('):analysis.index('\nfunction DecisionChoice(', analysis.index('function HumanDecisionWorkbench('))]
down=analysis[analysis.index('function DownstreamIntelligence('):analysis.index('\nfunction WorkspacePendingState(', analysis.index('function DownstreamIntelligence('))]
checks={
 'm08 root marker':'analysis-r97-m08' in analysis,
 'workspace type includes handoff':'| "handoff"' in analysis and '"human", "handoff"' in analysis,
 'handoff nav tab':'label:"Governed Handoff"' in analysis,
 'handoff zone':'selectedWorkspace === "handoff"' in down and 'AnalysisZone index="05" title="Governed handoff"' in down,
 'handoff component moved out of human':'GovernedLearningHandoff' not in human,
 'handoff component preserved in new zone':'<GovernedLearningHandoff run={run} learning={learning} authorities={authorities} onLearningChange={setLearning} />' in down,
 'human choices preserved':all(x in human for x in ['title="Affected"','title="Not affected"','title="Needs more investigation"']),
 'smart rationale preserved':'human-rationale-r97-m05' in human,
 'governed record preserved':'human-decision-record-r97-m06' in human and 'View governed record' in human,
 'atomic submission preserved':'Submit decisions' in human and 'allReady' in human,
 'overflow css marker':'UI-R97-M08 — Governed Handoff Tab + Human Decision Overflow Guard' in css,
 'governed meta safe rows':'grid-template-columns:minmax(88px,118px) minmax(0,1fr)' in css,
 'body width constrained':'.analysis-r97-m08 .human-decision-inline-body-r97-m07' in css and 'max-width:100%' in css,
 'responsive decision controls':'@media(max-width:980px)' in css and 'grid-template-columns:1fr' in css,
 'notes lineage':'Builds directly on approved UI-R97-M07' in notes,
 'notes no logic changes':'No changes to Qwen, LangGraph' in notes,
}
failed=[k for k,v in checks.items() if not v]
for k,v in checks.items(): print(('PASS' if v else 'FAIL'),k)
if failed: raise SystemExit('UI-R97-M08 verification failed: '+', '.join(failed))
print('UI-R97-M08 verification PASS')
