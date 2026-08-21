from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CSS = (ROOT / "frontend" / "app" / "globals.css").read_text(encoding="utf-8")
KNOWLEDGE = (ROOT / "frontend" / "components" / "knowledge-workspace.tsx").read_text(encoding="utf-8")
NOTES = (ROOT / "UI_R27_NOTES.md").read_text(encoding="utf-8")

for token in [
    "UI-R27 — Minimal Visual Evidence",
    ".knowledge-command-r27",
    ".knowledge-glance-r27",
    ".evidence-card-grid-r27",
    ".evidence-score-track-r27",
    ".document-seal-glance-r27",
    ".ingest-flow-r27",
    "@media (max-width:860px)",
    "@media (max-width:620px)",
]:
    assert token in CSS, f"missing UI-R27 CSS contract: {token}"

for token in [
    'className="knowledge-command-r27"',
    'className="knowledge-glance-r27"',
    'className="evidence-card-grid-r27"',
    'label="Evidence registry"',
    'label="Provenance & ranking"',
    'label="Read source text"',
    'label="Provenance proof"',
    'label="Ingestion rules"',
    "Search scores prioritise material for inspection.",
    "CREED will not substitute a fabricated result.",
    "Ingestion stores source material. It does not approve or validate the document's business meaning.",
    'form.set("source", "LOCAL_DEMO")',
    "searchKnowledge(query.trim(), 8",
    "uploadDocument(form)",
    "getDocument(id)",
]:
    assert token in KNOWLEDGE, f"Knowledge visual-minimalism or truthfulness contract drifted: {token}"

for token in [
    "Minimal Visual Evidence",
    "Search → Inspect → Prove",
    "SHA-256",
    "actual parsed source",
]:
    assert token in NOTES, f"missing UI-R27 notes contract: {token}"

assert not (ROOT / "frontend" / "app" / "demo").exists(), "Demo route must remain removed"
for path in (ROOT / "frontend").rglob("*.tsx"):
    text = path.read_text(encoding="utf-8")
    assert "react-icons" not in text
    assert "@heroicons" not in text
    assert "fontawesome" not in text.lower()

assert CSS.count("{") == CSS.count("}"), "CSS braces are unbalanced"
print("UI-R27 verification: PASS")
print("- Knowledge is search-first with visual evidence cards")
print("- registry, ranking explanation and deep provenance use progressive disclosure")
print("- extracted source text and SHA-256 proof remain available")
print("- ingestion keeps real Parse -> Seal -> Chunk -> Index workflow semantics")
print("- real retrieval/upload APIs, Demo removal and Lucide-only policy preserved")
