from pathlib import Path
root=Path(__file__).resolve().parents[1]
analysis=(root/'frontend/components/analysis-shell.tsx').read_text()
issue=(root/'frontend/components/issue-capsule-form.tsx').read_text()
advanced=(root/'backend/app/services/advanced.py').read_text()
css=(root/'frontend/app/globals.css').read_text()
notes=(root/'UI_R98_M01_NOTES.md').read_text()
ev=analysis[analysis.index('function EvidenceWorkbench('):analysis.index('\nfunction evidenceCitationTitle(',analysis.index('function EvidenceWorkbench('))]
checks={
 'lineage notes':'Builds directly on approved UI-R97-M09' in notes,
 'evidence accordion preserved':'evidence-accordion-list-r97-m09' in ev and 'setSelectedHitId(active ? null : result.id)' in ev,
 'collapsed chunk location removed':'<small>{location}</small>' not in ev,
 'collapsed metadata shown':'result.document_type' in ev and 'result.document_version' in ev and 'result.document_source' in ev,
 'match compact':'Math.round(result.final_score * 100)}%</em>' in ev and '% MATCH' not in ev[ev.index('candidate-accordion-list-r97-m07'):ev.index('candidate-accordion-body-r97-m07')],
 'location only expanded':'evidence-hit-location-r98-m01' in ev and 'evidenceCitationLocation(selected.citation)' in ev,
 'open source retained':'Open source' in ev and 'SourceEvidenceModal' in ev,
 'proof retained':'Proof & provenance' in ev,
 'retrieval context retained':'Retrieval context' in ev,
 'metadata serialized':all(x in advanced for x in ['"document_type"','"document_version"','"document_source"']),
 'four intake steps':'{ id: 4, label: "Review"' in issue and 'label: "Evidence"' not in issue.split('] as const;')[0],
 'old evidence step removed':'function StepEvidence(' not in issue,
 'optional evidence disclosure':'Attach additional evidence' in issue and 'AdditionalEvidenceControl' in issue,
 'review says governed retrieval':'CREED retrieves governed evidence after Save & analyse.' in issue,
 'save at step four':'step < 4' in issue and 'Math.min(4, current + 1)' in issue,
 'attachment upload preserved':'await uploadDocument(form)' in issue,
 'css marker':'UI-R98-M01 — Clean Evidence + frictionless issue creation' in css,
 'no governance semantics claim':'No change to Qwen, LangGraph, retrieval ranking' in notes,
}
failed=[k for k,v in checks.items() if not v]
for k,v in checks.items(): print(('PASS' if v else 'FAIL'),k)
if failed: raise SystemExit('UI-R98-M01 verification failed: '+', '.join(failed))
print('UI-R98-M01 verification PASS')
