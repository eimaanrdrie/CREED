from pathlib import Path
root=Path(__file__).resolve().parents[1]
ui=(root/'frontend/components/knowledge-workspace.tsx').read_text()
css=(root/'frontend/app/globals.css').read_text()
checks={
  'hybrid retrieval removed':'HYBRID RETRIEVAL' not in ui and 'Search evidence' not in ui,
  'inspect command removed':'<span>Inspect</span>' not in ui and 'mode === "inspect"' not in ui,
  'upload renamed':'<span>Upload</span>' in ui and 'Upload project evidence' in ui and 'Upload evidence' in ui,
  'repository list preserved':'Knowledge documents' in ui and 'knowledge-library-row-r98-m07' in ui,
  'preview opens from list':'onClick={()=>openDocument(doc.id)}' in ui and 'setPreviewOpen(true)' in ui,
  'original endpoint used':'getDocumentOriginalUrl(detail.id)' in ui,
  'hash verification required':'X-CREED-Original-Verified' in ui and 'X-CREED-Content-SHA256' in ui,
  'pdf inline preview':'kind==="pdf"' in ui and '<iframe' in ui,
  'text original preview':'kind==="text"' in ui and 'setRawText(await blob.text())' in ui,
  'docx preview path':'kind==="docx"' in ui and 'Open original file' in ui,
  'preview modal css':'knowledge-preview-modal-r98-m08' in css,
}
failed=[k for k,v in checks.items() if not v]
for k,v in checks.items(): print(('PASS' if v else 'FAIL'),k)
if failed: raise SystemExit('UI-R98-M08 verifier FAILED: '+', '.join(failed))
print('UI-R98-M08 verifier PASS')
