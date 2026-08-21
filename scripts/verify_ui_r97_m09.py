from pathlib import Path
root=Path(__file__).resolve().parents[1]
analysis=(root/'frontend/components/analysis-shell.tsx').read_text()
css=(root/'frontend/app/globals.css').read_text()
notes=(root/'UI_R97_M09_NOTES.md').read_text()
case=analysis[analysis.index('{workspace === "context"'):analysis.index('{workspace !== "context"', analysis.index('{workspace === "context"'))]
ev=analysis[analysis.index('function EvidenceWorkbench('):analysis.index('\nfunction evidenceCitationTitle(',analysis.index('function EvidenceWorkbench('))]
checks={
 'm09 root marker':'analysis-r97-m09' in analysis,
 'old case AI headline removed':'AI INTERPRETATION' not in case and 'Qwen understanding' not in case,
 'AI intake purpose explicit':'AI intake interpretation' in case and 'Structured extraction used for retrieval and catalog routing' in case,
 'AI collapsed disclosure':'case-context-ai-details-r97-m09' in case and '<summary>' in case,
 'Qwen verify preserved':'UnderstandingEditor' in case and '"Cancel" : "Verify"' in case,
 'Qwen rerun preserved':'runQwenOnly' in case and ('Re-run' in case or 'Run Qwen' in case),
 'evidence uses shared accordion':'candidate-accordion-list-r97-m07 evidence-accordion-list-r97-m09' in ev,
 'evidence rows toggle closed':'setSelectedHitId(active ? null : result.id)' in ev,
 'evidence all collapsed initially':'useState<string | null>(null)' in ev,
 'evidence master detail removed':'evidence-layout-r57' not in ev and 'evidence-inspector-r57' not in ev and 'evidence-master-r57' not in ev,
 'evidence row essentials':all(x in ev for x in ['result.rank','evidenceCitationTitle(result.citation)','evidenceCitationLocation(result.citation)','% MATCH','candidate-accordion-chevron-r97-m07']),
 'source excerpt retained':'RETRIEVED EXCERPT' in ev and 'selected.excerpt' in ev,
 'open source retained':'openSelectedSource()' in ev and 'Open source' in ev,
 'source modal preserved':'SourceEvidenceModal' in ev,
 'proof retained':'Proof & provenance' in ev and 'selectedDocumentDetail.content_hash' in ev,
 'retrieval context collapsed':'Retrieval context' in ev,
 'css marker':'UI-R97-M09 — Minimal Case Context + Evidence Accordions' in css,
 'notes lineage':'Builds directly on approved UI-R97-M08' in notes,
 'notes qwen purpose':'build retrieval query terms' in notes and 'catalog context' in notes,
 'notes no logic change':'No changes to backend evidence retrieval' in notes,
}
failed=[k for k,v in checks.items() if not v]
for k,v in checks.items(): print(('PASS' if v else 'FAIL'),k)
if failed: raise SystemExit('UI-R97-M09 verification failed: '+', '.join(failed))
print('UI-R97-M09 verification PASS')
