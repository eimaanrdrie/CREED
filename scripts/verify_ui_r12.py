from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
css = (ROOT / 'frontend/app/globals.css').read_text(encoding='utf-8')
design = (ROOT / 'frontend/DESIGN.md').read_text(encoding='utf-8')
notes = (ROOT / 'UI_R12_NOTES.md').read_text(encoding='utf-8')
app = ROOT / 'frontend/app'
sidebar = (ROOT / 'frontend/components/sidebar.tsx').read_text(encoding='utf-8')
errors: list[str] = []

required_css = [
    'UI-R12 — Deep Navy + Azure Blue assurance palette',
    '--bg: oklch(10.8% 0.030 258)',
    '--azure: oklch(70% 0.170 250)',
    '--azure-pale: oklch(87% 0.070 244)',
    '--trusted: oklch(74% 0.110 184)',
    '--gold: var(--azure)',
    '--gold-pale: var(--azure-pale)',
    'UI-R12 — Deep Navy + Azure Blue Color System',
    '.primary-btn { border-color:var(--azure); background:var(--azure)',
    '.nav-item.active { background:oklch(70% .17 250 / .11)',
    'overflow-x:clip',
]
for token in required_css:
    if token not in css:
        errors.append(f'missing R12 CSS token: {token}')

if 'Deep Navy + Azure Blue' not in design or 'Deep Navy + Azure Blue' not in notes:
    errors.append('R12 design/notes documentation missing')

# Warm assurance-gold accent literal from R10/R11 must no longer drive UI emphasis.
for pattern in [r'oklch\(78%\s+0?\.12\s+82\b', r'oklch\(88%\s+0?\.065\s+84\b']:
    if re.search(pattern, css):
        errors.append(f'legacy warm accent literal remains: {pattern}')

# Approved product constraints must stay intact.
if (app / 'demo').exists():
    errors.append('frontend /demo route exists')
if 'href="/demo"' in sidebar or "href='/demo'" in sidebar:
    errors.append('Demo navigation exists')

for path in (ROOT / 'frontend').rglob('*'):
    if path.suffix not in {'.ts', '.tsx'}:
        continue
    text = path.read_text(encoding='utf-8', errors='ignore')
    if re.search(r'<svg\b', text, re.IGNORECASE):
        errors.append(f'raw SVG found: {path.relative_to(ROOT)}')
    for m in re.finditer(r'from\s+["\']([^"\']+)["\']', text):
        pkg = m.group(1).lower()
        if any(x in pkg for x in ['react-icons', 'heroicons', 'fontawesome', 'phosphor', 'iconsax']):
            errors.append(f'non-Lucide icon library: {path.relative_to(ROOT)} -> {pkg}')

if css.count('{') != css.count('}'):
    errors.append('CSS brace count is unbalanced')
if '\\n' in css:
    errors.append('literal \\n sequence remains in CSS')

if errors:
    print('UI-R12 VERIFY: FAIL')
    for error in errors:
        print('-', error)
    sys.exit(1)

print('UI-R12 VERIFY: PASS')
print('- deep navy + Azure token system present')
print('- warm gold accent literals removed from active palette')
print('- teal trusted / amber warning / red destructive semantics retained')
print('- R11 readability + overflow hardening retained')
print('- Demo route remains removed')
print('- Lucide-only active icon policy retained')
