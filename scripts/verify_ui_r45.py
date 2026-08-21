from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TSX = (ROOT / "frontend/components/audit-workspace.tsx").read_text(encoding="utf-8")
CSS = (ROOT / "frontend/app/globals.css").read_text(encoding="utf-8")
NOTES = (ROOT / "UI_R45_NOTES.md").read_text(encoding="utf-8")

required_tsx = [
    'const [eventQuery, setEventQuery] = useState("")',
    'className="audit-stream-head-r45"',
    'className="audit-stream-toolbar-r45"',
    'className="audit-event-search-r45"',
    'className="audit-filter-row-r29 audit-category-row-r45"',
    'audit-event-stream-list-r45',
    'audit-stream-event-r45',
    'Search events, status, actor or model…',
    'Clear filters',
]
missing = [x for x in required_tsx if x not in TSX]
assert not missing, f"Missing R45 Audit event-stream markup: {missing}"

required_css = [
    "UI-R45 — Audit Event Stream Redesign",
    ".audit-stream-r45",
    ".audit-event-search-r45",
    ".audit-category-row-r45",
    ".audit-event-stream-list-r45",
    ".audit-stream-event-r45",
    "height:clamp(320px,52vh,620px)",
]
missing = [x for x in required_css if x not in CSS]
assert not missing, f"Missing R45 CSS contract: {missing}"

assert "forensic event stream" in NOTES
assert "no fake audit records" in NOTES
assert 'getAudit(' in TSX, "Audit must remain backend-backed"
assert 'data.timeline.filter' in TSX, "R45 search/filter must operate on persisted timeline data"
print("UI-R45 verifier: PASS")
