from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TSX = (ROOT / "frontend/components/audit-workspace.tsx").read_text(encoding="utf-8")
CSS = (ROOT / "frontend/app/globals.css").read_text(encoding="utf-8")
NOTES = (ROOT / "UI_R47_NOTES.md").read_text(encoding="utf-8")

required_tsx = [
    'audit-deep-proof-r47',
    'RUN-SCOPED PROOF',
    'Deep evidence & governance',
    'audit-deep-grid-r47',
    'Agent execution',
    'Qwen execution',
    'Evidence accessed',
    'Impact priority',
    'Human authority',
    'Governance artefacts',
    'audit-impact-track-r47',
    'Priority score guides investigation. It is not a defect verdict.',
]
missing = [x for x in required_tsx if x not in TSX]
assert not missing, f"Missing R47 deep-proof markup: {missing}"

required_css = [
    'UI-R47 — Audit Deep Evidence + Governance Polish',
    '.audit-deep-proof-r47',
    '.audit-deep-group-r47',
    '.audit-evidence-row-r47',
    '.audit-impact-track-r47',
    '.audit-human-group-r47',
    '.audit-governance-group-r47',
    '@media (max-width:980px)',
]
missing = [x for x in required_css if x not in CSS]
assert not missing, f"Missing R47 CSS contract: {missing}"

assert 'no fake qwen' in NOTES.lower()
assert 'getAudit(' in TSX, 'Audit must remain backend-backed'
assert 'getDocument(' in TSX, 'Evidence inspection must remain backend-backed'
assert 'selected.content_hash' in TSX, 'Persisted integrity metadata must remain visible'
assert 'i.impact_score' in TSX, 'Impact score must remain data-backed'
assert 'h.reason' in TSX, 'Human rationale must remain visible'
assert 'g.content_hash' in TSX, 'Governance integrity metadata must remain visible'
print('UI-R47 verifier: PASS')
