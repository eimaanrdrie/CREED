from pathlib import Path

root = Path(__file__).resolve().parents[1]
analysis = (root / 'frontend/components/analysis-shell.tsx').read_text()
css = (root / 'frontend/app/globals.css').read_text()
notes = (root / 'UI_R97_M01_NOTES.md').read_text()

checks = {
    'candidate summary marker': 'investigation-candidate-summary-r97-m01' in analysis,
    'current column': '<span>Current</span>' in analysis,
    'requested column': '<span>Requested</span>' in analysis,
    'result column': '<span>Result</span>' in analysis,
    'current comparison value': 'comparison.current_state' in analysis,
    'requested comparison value': 'comparison.requested_state' in analysis,
    'technical result label': 'configurationTechnicalLabel(comparison.technical_result)' in analysis,
    'minimal CSS': 'UI-R97-M01 — Minimal Investigation Candidate Summary' in css,
    'module notes': 'Investigation only' in notes,
}

failed = [name for name, ok in checks.items() if not ok]
for name, ok in checks.items():
    print(f"{'PASS' if ok else 'FAIL'}  {name}")
if failed:
    raise SystemExit('UI-R97-M01 verification failed: ' + ', '.join(failed))
print('UI-R97-M01 verification PASS')
