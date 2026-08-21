from pathlib import Path

root = Path(__file__).resolve().parents[1]
analysis = (root / 'frontend/components/analysis-shell.tsx').read_text()
css = (root / 'frontend/app/globals.css').read_text()
notes = (root / 'UI_R97_M03_NOTES.md').read_text()

checks = {
    'm01 retained': 'investigation-candidate-summary-r97-m01' in analysis,
    'm02 retained': 'investigation-selected-summary-r97-m02' in analysis,
    'm03 stack marker': 'investigation-detail-stack-r97-m03' in analysis,
    'AI analysis disclosure': '>AI analysis</span>' in analysis,
    'source evidence disclosure': '>Source evidence</span>' in analysis,
    'proof provenance disclosure': '>Proof & provenance</span>' in analysis,
    'source opens retained': 'openInvestigationSource(documentId)' in analysis,
    'source evidence outside AI body': analysis.index('>Source evidence</span>') > analysis.index('>AI analysis</span>'),
    'priority moved into proof': 'investigation-priority-r97-m03' in analysis,
    'old focus grid removed from selected candidate': 'investigation-focus-grid-r58 investigation-focus-grid-r66' not in analysis,
    'old standalone inspect proof removed': 'ProgressiveDisclosure label="Inspect proof" meta={`${evidenceRefs.length} evidence refs`}' not in analysis,
    'm03 CSS': 'UI-R97-M03 — Expandable investigation details' in css,
    'module notes': 'Builds directly on approved UI-R97-M02' in notes,
}

failed = [name for name, ok in checks.items() if not ok]
for name, ok in checks.items():
    print(f"{'PASS' if ok else 'FAIL'}  {name}")
if failed:
    raise SystemExit('UI-R97-M03 verification failed: ' + ', '.join(failed))
print('UI-R97-M03 verification PASS')
