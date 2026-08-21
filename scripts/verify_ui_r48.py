from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TSX = (ROOT / 'frontend/components/audit-workspace.tsx').read_text(encoding='utf-8')
CSS = (ROOT / 'frontend/app/globals.css').read_text(encoding='utf-8')
NOTES = (ROOT / 'UI_R48_NOTES.md').read_text(encoding='utf-8')

required_tsx = [
    'const AUDIT_PAGE_SIZE = 6',
    'const [auditPage, setAuditPage] = useState(1)',
    'const pagedTimeline = timeline.slice',
    'audit-pagination-r48',
    'audit-page-number-r48',
    'aria-label="Audit event pages"',
    'aria-current={safeAuditPage===item?"page":undefined}',
    'pagedTimeline.map',
]
missing = [x for x in required_tsx if x not in TSX]
assert not missing, f'Missing R48 pagination markup/logic: {missing}'

required_css = [
    'UI-R48 — Audit numbered pagination',
    '.audit-event-page-r48',
    '.audit-pagination-r48',
    '.audit-page-number-r48',
    '.audit-page-step-r48',
    '.audit-page-ellipsis-r48',
    'overflow-y:visible',
]
missing = [x for x in required_css if x not in CSS]
assert not missing, f'Missing R48 CSS contract: {missing}'

# R48 must remove the scroll trigger from the live audit-list markup.
assert 'audit-event-stream-list-r45" data-r42-scroll="true"' not in TSX
assert 'getAudit(' in TSX
assert 'setSelected(item)' in TSX
assert 'No audit records' in NOTES
print('UI-R48 verifier: PASS')
