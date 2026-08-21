from pathlib import Path

root = Path(__file__).resolve().parents[1]
component = (root / 'frontend/components/change-radar-workspace.tsx').read_text(encoding='utf-8')
css = (root / 'frontend/app/globals.css').read_text(encoding='utf-8')
checks = {
    'investigation retrieval': 'getRunInvestigations' in component,
    'muted technical states': 'ALREADY_MATCHES' in component and 'ALREADY_PROTECTED' in component,
    'human not affected mapping': 'NOT_AFFECTED' in component,
    'active decision mapping': 'AFFECTED' in component,
    'edge muted class': 'radar-edge-muted' in component,
    'edge active class': 'radar-edge-active' in component,
    'dashed muted relationship': 'strokeDasharray: isMuted ? "7 6"' in component,
    'muted node css': '.creed-radar-node.action-muted.node-implementation' in css,
    'active node css': '.creed-radar-node.action-active.node-implementation' in css,
    'legend no change': 'No change needed' in component,
}
failed = [name for name, ok in checks.items() if not ok]
for name, ok in checks.items():
    print(('PASS' if ok else 'FAIL'), name)
if failed:
    raise SystemExit('UI-R99-M05 verification failed: ' + ', '.join(failed))
print('UI-R99-M05 PASS')
