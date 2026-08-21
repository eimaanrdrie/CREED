from pathlib import Path
root=Path(__file__).resolve().parents[1]
analysis=(root/'frontend/components/analysis-shell.tsx').read_text()
css=(root/'frontend/app/globals.css').read_text()
notes=(root/'UI_R97_M07_NOTES.md').read_text()

human=analysis[analysis.index('function HumanDecisionWorkbench('):analysis.index('\nfunction DecisionChoice(', analysis.index('function HumanDecisionWorkbench('))]
inv=analysis[analysis.index('function InvestigationWorkbench('):analysis.index('\nfunction CrossBankConfigurationSummary(', analysis.index('function InvestigationWorkbench('))]
checks={
 'm07 root marker':'analysis-r97-m07' in analysis,
 'shared list used twice':analysis.count('candidate-accordion-list-r97-m07') >= 2,
 'shared trigger used twice':analysis.count('candidate-accordion-trigger-r97-m07') >= 2,
 'chevron disclosure':analysis.count('candidate-accordion-chevron-r97-m07') >= 2 and 'ChevronDown' in analysis,
 'investigation toggles closed':'setSelectedImplementationId(active ? null : item.implementation_id)' in inv,
 'human toggles closed':'setSelectedReviewId(active ? null : item.id)' in human,
 'investigation no cross-bank summary':'CrossBankConfigurationSummary' not in inv,
 'human no cross-bank summary':'CrossBankConfigurationSummary' not in human,
 'old investigation matrix removed':'investigation-candidate-summary-r97-m01' not in inv,
 'old selected summary removed':'investigation-selected-summary-r97-m02' not in inv,
 'old human master detail removed':'authority-focus-layout-r59' not in human and 'authority-master-r53' not in human,
 'investigation details retained':all(x in inv for x in ['>AI analysis</span>','>Source evidence</span>','>Proof & provenance</span>']),
 'open source retained':'openInvestigationSource(documentId)' in inv,
 'human choices retained':all(x in human for x in ['title="Affected"','title="Not affected"','title="Needs more investigation"']),
 'smart rationale retained':'human-rationale-r97-m05' in human,
 'governed record retained':'human-decision-record-r97-m06' in human and 'View governed record' in human,
 'atomic submit retained':'Submit decisions' in human and 'allReady' in human,
 'shared CSS marker':'UI-R97-M07 — Unified Candidate Accordions' in css,
 'notes lineage':'Builds directly on approved UI-R97-M06' in notes,
 'notes scope boundary':'No changes to Qwen, LangGraph' in notes,
}
failed=[k for k,v in checks.items() if not v]
for k,v in checks.items(): print(('PASS' if v else 'FAIL'),k)
if failed: raise SystemExit('UI-R97-M07 verification failed: '+', '.join(failed))
print('UI-R97-M07 verification PASS')
