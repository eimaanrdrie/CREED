from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TSX = (ROOT / "frontend/components/audit-workspace.tsx").read_text(encoding="utf-8")
CSS = (ROOT / "frontend/app/globals.css").read_text(encoding="utf-8")
NOTES = (ROOT / "UI_R46_NOTES.md").read_text(encoding="utf-8")

required_tsx = [
    'audit-proof-pane-r46',
    'audit-proof-inspector-r46',
    'PROOF INSPECTOR',
    'audit-proof-trace-r46',
    'Persisted audit',
    'PROOF FACTS',
    'Persisted fields only',
    'audit-proof-actionbar-r46',
    'Observable metadata only · no hidden chain-of-thought',
]
missing = [x for x in required_tsx if x not in TSX]
assert not missing, f"Missing R46 proof-inspector markup: {missing}"

required_css = [
    'UI-R46 — Audit Proof Inspector Redesign',
    '.audit-proof-inspector-r46',
    '.audit-proof-inspector-head-r46',
    '.audit-proof-trace-r46',
    '.audit-proof-narrative-r46',
    '.audit-proof-facts-r46',
    '.audit-proof-actionbar-r46',
    'repeat(auto-fit,minmax(min(100%,170px),1fr))',
]
missing = [x for x in required_css if x not in CSS]
assert not missing, f"Missing R46 CSS contract: {missing}"

assert 'forensic proof inspector' in NOTES
assert 'no fake Qwen' in NOTES
assert 'getAudit(' in TSX, 'Audit must remain backend-backed'
assert 'getDocument(' in TSX, 'Evidence inspection must remain backend-backed'
assert 'selected.content_hash' in TSX, 'Persisted integrity metadata must remain visible'
print('UI-R46 verifier: PASS')
