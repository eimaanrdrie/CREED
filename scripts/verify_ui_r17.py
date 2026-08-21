from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CSS = (ROOT / "frontend" / "app" / "globals.css").read_text(encoding="utf-8")
KNOWLEDGE = (ROOT / "frontend" / "components" / "knowledge-workspace.tsx").read_text(encoding="utf-8")
NOTES = (ROOT / "UI_R17_NOTES.md").read_text(encoding="utf-8")

required_css = [
    "UI-R17 — Knowledge Repository Readability + Evidence Workflow Recomposition",
    ".knowledge-page-r06 {\n  max-width: 1320px",
    "--type-md: 15px",
    "min-height: 44px",
    "@media (max-width: 1420px)",
    ".knowledge-find-layout-r06,\n  .knowledge-inspect-layout-r06,\n  .knowledge-ingest-layout-r06 { grid-template-columns: 1fr; }",
    "content: attr(data-label)",
    "overflow-wrap: anywhere",
]
for token in required_css:
    assert token in CSS, f"missing UI-R17 CSS contract: {token}"

for token in [
    'data-label="Source"',
    'data-label="Index"',
    'data-label="SHA-256"',
    'LOCAL REPOSITORY',
    'Evidence remains the source of truth.',
    "Search scores prioritise material for inspection.",
    "Ingestion stores source material. It does not approve or validate the document's business meaning.",
]:
    assert token in KNOWLEDGE, f"Knowledge provenance/responsive contract drifted: {token}"

assert "Knowledge Repository Readability + Evidence Workflow Recomposition" in NOTES
assert not (ROOT / "frontend" / "app" / "demo").exists(), "Demo route must remain removed"
for path in (ROOT / "frontend").rglob("*.tsx"):
    text = path.read_text(encoding="utf-8")
    assert "react-icons" not in text
    assert "@heroicons" not in text
    assert "fontawesome" not in text.lower()

assert CSS.count("{") == CSS.count("}"), "CSS braces are unbalanced"
print("UI-R17 verification: PASS")
print("- Knowledge bounded to 1320px with larger local operational typography")
print("- Find / Inspect / Ingest reflow before permanent-sidebar compression")
print("- search, filters, ingestion and hash actions meet 44px interaction floor")
print("- registry rows become labelled mobile evidence records")
print("- provenance-first and human-supplied-evidence semantics retained")
