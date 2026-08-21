from pathlib import Path
root=Path(__file__).resolve().parents[1]
docs=(root/'backend/app/api/documents.py').read_text()
main=(root/'backend/app/main.py').read_text()
ui=(root/'frontend/components/analysis-shell.tsx').read_text()
checks={
'demo stale path rebasing':'metadata.get("synthetic") is True' in docs and 'rebased = (demo_root / safe_name).resolve()' in docs,
'hash remains enforced':'ORIGINAL_FILE_HASH_MISMATCH' in docs,
'cors exposes verified header':'expose_headers=' in main and 'X-CREED-Original-Verified' in main,
'cors exposes hash header':'X-CREED-Content-SHA256' in main,
'frontend verifies status header':'response.headers.get("X-CREED-Original-Verified")' in ui,
'frontend verifies hash header':'response.headers.get("X-CREED-Content-SHA256")' in ui,
'pdf uses verified blob':'URL.createObjectURL(blob)' in ui and 'Original PDF' in ui,
'backend error detail surfaced':'body?.detail' in ui,
'no premature verified claim':'Original bytes hash-verified' not in ui,
}
failed=[k for k,v in checks.items() if not v]
for k,v in checks.items(): print(('PASS' if v else 'FAIL'),k)
if failed: raise SystemExit('UI-R96 REV2 verifier FAIL: '+', '.join(failed))
print('UI-R96 REV2 verifier PASS')
