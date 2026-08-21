from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
css = (ROOT / 'frontend/app/globals.css').read_text()
sidebar = (ROOT / 'frontend/components/sidebar.tsx').read_text()
app = ROOT / 'frontend/app'
errors=[]

required = [
    '--type-2xs: 11px',
    '--type-body: 15px',
    'UI-R11 — Readability Scale + Overflow Hardening',
    'overflow-x:clip',
    '.overview-hero h1 { max-width:900px; font-size:clamp(36px,3.25vw,50px)',
    '@media (max-width:760px)',
    '--type-body:16px',
]
for item in required:
    if item not in css:
        errors.append(f'missing R11 marker: {item}')

# No frontend /demo route may return.
if (app / 'demo').exists():
    errors.append('frontend /demo route exists')
if 'href="/demo"' in sidebar or "href='/demo'" in sidebar:
    errors.append('Demo navigation exists')

# Active icon imports remain Lucide-only in TS/TSX source.
for path in (ROOT/'frontend').rglob('*'):
    if path.suffix not in {'.ts','.tsx'}:
        continue
    text=path.read_text(errors='ignore')
    for m in re.finditer(r'from\s+["\']([^"\']+)["\']', text):
        pkg=m.group(1)
        if any(x in pkg.lower() for x in ['react-icons','heroicons','fontawesome','phosphor']):
            errors.append(f'non-Lucide icon library in {path.relative_to(ROOT)}: {pkg}')

# Legacy microscopic numeric font declarations should have been normalized into tokens.
for m in re.finditer(r'font-size\s*:\s*(\d+(?:\.\d+)?)px', css):
    if float(m.group(1)) < 13:
        errors.append(f'raw font-size below 13px remains: {m.group(0)}')
        break
for m in re.finditer(r'font\s*:[^;{}]*?\b(\d+(?:\.\d+)?)px(?:/|\s)', css):
    if float(m.group(1)) < 13:
        errors.append(f'raw font shorthand below 13px remains: {m.group(0)[:80]}')
        break

if errors:
    print('UI-R11 VERIFY: FAIL')
    for e in errors:
        print('-',e)
    sys.exit(1)
print('UI-R11 VERIFY: PASS')
print('- system-wide readability tokens present')
print('- legacy microscopic font declarations normalized')
print('- viewport overflow hardening present')
print('- Overview responsive composition hardened')
print('- Demo route remains removed')
print('- no secondary active icon library detected')
