from pathlib import Path

root = Path(__file__).resolve().parents[1]
analysis = (root / 'frontend/components/analysis-shell.tsx').read_text()
css = (root / 'frontend/app/globals.css').read_text()
notes = (root / 'UI_R97_M04_NOTES.md').read_text()

checks = {
    'm01 retained': 'investigation-candidate-summary-r97-m01' in analysis,
    'm02 retained': 'investigation-selected-summary-r97-m02' in analysis,
    'm03 retained': 'investigation-detail-stack-r97-m03' in analysis,
    'm04 decision header': 'human-decision-card-head-r97-m04' in analysis,
    'minimal advisory block': 'human-decision-card-advisory-r97-m04' in analysis,
    'three governed decisions retained': all(token in analysis for token in ['value="AFFECTED"', 'value="NOT_AFFECTED"', 'value="NEEDS_MORE_INVESTIGATION"']),
    'technical basis disclosure': 'ProgressiveDisclosure label="View technical basis"' in analysis,
    'comparison moved inside disclosure': analysis.index('ProgressiveDisclosure label="View technical basis"') < analysis.index('ConfigurationComparisonPanel comparison={selectedComparison}', analysis.index('ProgressiveDisclosure label="View technical basis"')),
    'old always-visible selected signals removed': 'authority-selected-signals-r59">\n            <span><small>Priority' not in analysis,
    'queue priority removed': '` · Priority ${priority}`' not in analysis,
    'rationale logic retained': 'selectedConsistency?.contradiction' in analysis and 'R9406_CONTRADICTION_RATIONALE_MIN_CHARS' in analysis,
    'atomic submit retained': 'Submit decisions' in analysis,
    'm04 CSS': 'UI-R97-M04 — Minimalist Human Decision card' in css,
    'module notes': 'Builds directly on approved UI-R97-M03' in notes,
}

failed = [name for name, ok in checks.items() if not ok]
for name, ok in checks.items():
    print(f"{'PASS' if ok else 'FAIL'}  {name}")
if failed:
    raise SystemExit('UI-R97-M04 verification failed: ' + ', '.join(failed))
print('UI-R97-M04 verification PASS')
