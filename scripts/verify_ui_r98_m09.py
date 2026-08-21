from pathlib import Path
root=Path(__file__).resolve().parents[1]
ui=(root/'frontend/components/knowledge-workspace.tsx').read_text()
css=(root/'frontend/app/globals.css').read_text()
checks={
  'source preview header':'SOURCE PREVIEW' in ui,
  'original preview tab':'Original preview' in ui and 'activeView==="original"' in ui,
  'extracted text tab':'Extracted text' in ui and 'activeView==="extracted"' in ui,
  'original default':'useState<"original"|"extracted">("original")' in ui,
  'hash verification preserved':'X-CREED-Original-Verified' in ui and 'X-CREED-Content-SHA256' in ui,
  'pdf original preserved':'kind==="pdf"' in ui and '<iframe' in ui,
  'text original preserved':'kind==="text"' in ui and 'setRawText(await blob.text())' in ui,
  'extracted representation labelled':'Parser-derived representation used for indexing and retrieval.' in ui,
  'preview tabs css':'knowledge-preview-tabs-r98-m09' in css,
}
failed=[k for k,v in checks.items() if not v]
for k,v in checks.items(): print(('PASS' if v else 'FAIL'),k)
if failed: raise SystemExit('UI-R98-M09 verifier FAILED: '+', '.join(failed))
print('UI-R98-M09 verifier PASS')
