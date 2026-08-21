from pathlib import Path
root = Path(__file__).resolve().parents[1]
css = (root / 'frontend/app/globals.css').read_text()
tsx = (root / 'frontend/components/analysis-shell.tsx').read_text()
assert 'analysis-r76-rev1' in tsx, 'Missing R76 REV1 root scope class'
required = [
    'UI-R76 REV1 — CASE CONTEXT SPACING + NEUTRAL AI TYPOGRAPHY',
    '--context-panel-pad:20px;',
    '.analysis-r76-rev1 .case-context-pane-head-r56 {',
    'min-height:64px;',
    '.analysis-r76-rev1 .case-context-title-r56 > svg,',
    '.analysis-r76-rev1 .case-source-excerpt-r56 {',
    'min-height:116px;',
    '.analysis-r76-rev1 .qwen-context-fields-r64 {',
]
for token in required:
    assert token in css, f'Missing CSS token: {token}'
print('UI-R76 REV1 verifier: PASS')
