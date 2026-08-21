from pathlib import Path
root=Path(__file__).resolve().parents[1]
sidebar=(root/'frontend/components/sidebar.tsx').read_text()
knowledge=(root/'frontend/components/knowledge-workspace.tsx').read_text()
page=(root/'frontend/app/approved-knowledge/page.tsx').read_text()
ui=(root/'frontend/components/approved-knowledge-workspace.tsx').read_text()
api=(root/'frontend/lib/api.ts').read_text()
css=(root/'frontend/app/globals.css').read_text()
checks={
 'evidence repository nav':'Evidence Repository' in sidebar and 'href: "/knowledge"' in sidebar,
 'approved knowledge nav':'Approved Knowledge' in sidebar and '/approved-knowledge' in sidebar,
 'knowledge renamed':'<h1>Evidence Repository</h1>' in knowledge and '<h2>Evidence documents</h2>' in knowledge,
 'approved page':'active="Approved Knowledge"' in page,
 'approved-only filter':'.filter((version) => version.status === "APPROVED")' in ui,
 'explicit use separate':'method_version_id === version.id' in ui and 'Approval and use are shown separately' in ui,
 'receipt detail api':'getAdoptionReceipt' in api and '/adoption-receipts/${encodeURIComponent(receiptId)}' in api,
 'receipt surface':'Signed adoption receipt' in ui and 'approval_reason' in ui and 'content_hash' in ui,
 'responsive css':'approved-knowledge-row-r99-m01' in css and '@media(max-width:600px)' in css,
 'method registry retained':'{ label: "Methods", icon: GitBranch, href: "/methods" }' in sidebar,
}
failed=[k for k,v in checks.items() if not v]
for k,v in checks.items(): print(('PASS' if v else 'FAIL'),k)
if failed: raise SystemExit('UI-R99-M01 verifier FAILED: '+', '.join(failed))
print('UI-R99-M01 verifier PASS')
