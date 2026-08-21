from pathlib import Path
root=Path(__file__).resolve().parents[1]
sidebar=(root/'frontend/components/sidebar.tsx').read_text()
recalls=(root/'frontend/components/recalls-workspace.tsx').read_text()
notice=(root/'frontend/components/recall-notice-workspace.tsx').read_text()
css=(root/'frontend/app/globals.css').read_text()
api=(root/'frontend/lib/api.ts').read_text()
checks={
 'knowledge recall nav':'{ label: "Knowledge Recall", icon: History, href: "/recalls" }' in sidebar,
 'workspace active label':'active="Knowledge Recall"' in recalls and 'active="Knowledge Recall"' in notice,
 'start recall action':'Start recall' in recalls and 'Authorize recall' in recalls,
 'no user revoke action':'Revoke knowledge' not in recalls and 'Revoke approved knowledge' not in recalls,
 'revoked is outcome':'resulting knowledge status: REVOKED' in recalls and 'REVOKED is the resulting knowledge status' in recalls,
 'three minimalist views':'Active recalls' in recalls and 'Revoked knowledge' in recalls and '>History <span>' in recalls,
 'signed notice preserved':'Signed Recall Notice' in recalls and 'Signed Recall Notice' in notice,
 'scope enforcement preserved':'Signed adoption boundary' in recalls and 'selectedPolicyReady' in recalls,
 'authority preserved':'can_authorize_recall' in recalls and 'Recall Authority' in recalls,
 'radar hidden from recall UI':'change-radar' not in recalls and 'change-radar' not in notice,
 'backend compatibility':'revokeMethodVersion' in recalls and '/method-versions/${encodeURIComponent(versionId)}/revoke' in api,
 'minimal recall css':'knowledge-recall-row-r99-m02' in css and 'knowledge-recall-tabs-r99-m02' in css,
}
failed=[k for k,v in checks.items() if not v]
for k,v in checks.items(): print(('PASS' if v else 'FAIL'),k)
if failed: raise SystemExit('UI-R99-M02 verifier FAILED: '+', '.join(failed))
print('UI-R99-M02 verifier PASS')
