from pathlib import Path

root = Path(__file__).resolve().parents[1]
analysis = (root / "frontend/components/analysis-shell.tsx").read_text()
css = (root / "frontend/app/globals.css").read_text()
notes = (root / "UI_R95_REV1_NOTES.md").read_text()
design = (root / "frontend/DESIGN.md").read_text()

checks = {
    "r95 analysis scope marker": "analysis-r95-rev1" in analysis,
    "evidence open source button": 'className="evidence-open-source-r65" type="button"' in analysis,
    "legacy evidence knowledge navigation removed": 'href={`/knowledge?document=${selected.document_id}`}' not in analysis,
    "source modal component": "function SourceEvidenceModal" in analysis,
    "modal full stored source": "FULL STORED SOURCE" in analysis and "detail.extracted_text" in analysis,
    "modal sha proof": "detail.content_hash" in analysis,
    "investigation receives evidence": "investigations={investigations} evidence={evidence}" in analysis,
    "ai analysis source section": "SOURCE EVIDENCE" in analysis and "investigation-ai-sources-r95" in analysis,
    "investigation source opens stored document": "openInvestigationSource" in analysis and "getDocument(documentId)" in analysis,
    "dark modal css": ".analysis-source-modal-r95" in css and "background:var(--panel);" in css,
    "investigation source css": ".investigation-source-card-r95" in css,
    "notes candidate": "CANDIDATE_AWAITING_APPROVAL" in notes,
    "design contract": "UI-R95 REV1" in design and "In-place source provenance" in design,
}

failed = [name for name, ok in checks.items() if not ok]
for name, ok in checks.items():
    print(("PASS" if ok else "FAIL"), name)
if failed:
    raise SystemExit("UI-R95 REV1 verifier FAIL: " + ", ".join(failed))
print("UI-R95 REV1 verifier PASS")
