from pathlib import Path

root = Path(__file__).resolve().parents[1]
analysis = (root / "frontend/components/analysis-shell.tsx").read_text()
api = (root / "frontend/lib/api.ts").read_text()
css = (root / "frontend/app/globals.css").read_text()
backend = (root / "backend/app/api/documents.py").read_text()
notes = (root / "UI_R96_REV1_NOTES.md").read_text()
design = (root / "frontend/DESIGN.md").read_text()

a = {
    "r96 scope marker": "analysis-r96-rev1" in analysis,
    "two fidelity tabs": "Original document" in analysis and "Extracted text" in analysis,
    "original defaults active": 'useState<"original" | "extracted">("original")' in analysis,
    "pdf original iframe": "analysis-source-original-frame-r96" in analysis and "getDocumentOriginalUrl" in analysis,
    "text fetches original endpoint": 'response.headers.get("X-CREED-Original-Verified")' in analysis,
    "docx fidelity boundary": "browser cannot render Word layout with guaranteed fidelity" in analysis,
    "extracted output explicitly separate": "EXTRACTED TEXT" in analysis and "detail.extracted_text" in analysis,
    "frontend original url": "/original`" in api and "getDocumentOriginalUrl" in api,
    "backend original endpoint": '@router.get("/{document_id}/original")' in backend,
    "backend sha recalculation": "hashlib.sha256()" in backend and "ORIGINAL_FILE_HASH_MISMATCH" in backend,
    "backend path restriction": "ORIGINAL_FILE_PATH_NOT_ALLOWED" in backend,
    "backend verified header": '"X-CREED-Original-Verified": "true"' in backend,
    "r96 css": ".analysis-source-view-tabs-r96" in css and ".analysis-source-original-frame-r96 iframe" in css,
    "notes candidate": "CANDIDATE_AWAITING_APPROVAL" in notes,
    "design contract": "UI-R96 REV1" in design and "Original source fidelity" in design,
}
failed = [name for name, ok in a.items() if not ok]
for name, ok in a.items():
    print(("PASS" if ok else "FAIL"), name)
if failed:
    raise SystemExit("UI-R96 REV1 verifier FAIL: " + ", ".join(failed))
print("UI-R96 REV1 verifier PASS")
