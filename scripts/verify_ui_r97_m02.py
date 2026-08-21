from pathlib import Path

root = Path(__file__).resolve().parents[1]
analysis = (root / 'frontend/components/analysis-shell.tsx').read_text()
css = (root / 'frontend/app/globals.css').read_text()
notes = (root / 'UI_R97_M02_NOTES.md').read_text()

checks = {
    'm01 retained': 'investigation-candidate-summary-r97-m01' in analysis,
    'selected summary marker': 'investigation-selected-summary-r97-m02' in analysis,
    'selected candidate kicker': 'SELECTED CANDIDATE' in analysis,
    'current requested flow': 'investigation-selected-flow-r97-m02' in analysis,
    'change explanation': 'current configuration differs from the requested state' in analysis,
    'matching explanation': 'already matches the requested state' in analysis,
    'protected explanation': 'equivalent protection is already in place' in analysis,
    'reconciliation explanation': 'requires reconciliation before a reliable configuration decision' in analysis,
    'old duplicate selected header removed': 'investigation-selected-signals-r58 investigation-selected-signals-r66' not in analysis,
    'old top comparison call removed': 'selectedComparison && <ConfigurationComparisonPanel comparison={selectedComparison} evidenceCount={evidenceRefs.length}' not in analysis,
    'm02 CSS': 'UI-R97-M02 — Minimal selected candidate analysis' in css,
    'module notes': 'Builds directly on approved UI-R97-M01' in notes,
}

failed = [name for name, ok in checks.items() if not ok]
for name, ok in checks.items():
    print(f"{'PASS' if ok else 'FAIL'}  {name}")
if failed:
    raise SystemExit('UI-R97-M02 verification failed: ' + ', '.join(failed))
print('UI-R97-M02 verification PASS')
