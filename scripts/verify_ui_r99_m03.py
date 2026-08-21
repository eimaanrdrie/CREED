from pathlib import Path
root=Path(__file__).resolve().parents[1]
config=(root/'backend/app/core/config.py').read_text()
docs=(root/'backend/app/api/documents.py').read_text()
deploy=(root/'frontend/components/deployment-registry-workspace.tsx').read_text()
checks={
 'relative storage anchored':'backend_root = Path(__file__).resolve().parents[2]' in config and 'return (backend_root / path).resolve()' in config,
 'canonical uploaded recovery':'upload_root / document_id / safe_name' in docs,
 'legacy relative recovery':'Path.cwd() / raw' in docs and 'backend_root / raw' in docs,
 'sha remains mandatory':'_sha256_file(candidate) == item.content_hash' in docs and 'ORIGINAL_FILE_HASH_MISMATCH' in docs,
 'governed root boundary':'_path_within(resolved, upload_root)' in docs and '_path_within(resolved, demo_root)' in docs,
 'no locale dependent deployment format':'Intl.DateTimeFormat(undefined' not in deploy,
 'deterministic utc deployment format':'getUTCDate()' in deploy and 'getUTCHours()' in deploy and ' UTC`' in deploy,
}
failed=[k for k,v in checks.items() if not v]
for k,v in checks.items(): print(('PASS' if v else 'FAIL'),k)
if failed: raise SystemExit('UI-R99-M03 verifier FAILED: '+', '.join(failed))
print('UI-R99-M03 verifier PASS')
