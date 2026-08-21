from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
css = (ROOT / "frontend/app/globals.css").read_text(encoding="utf-8").replace('@import "tailwindcss";','',1)
out = ROOT / "scripts/fixtures/ui_r90_rev1_modules_harness.html"

def ico():
    return '<span class="preview-ico-r90" aria-hidden="true"></span>'

flyout_items = [
    ("Products", "Delivery product catalog"),
    ("Modules", "Product capability catalog"),
    ("Clients", "Organisations and counterparties"),
    ("Implementations", "Client delivery instances"),
    ("Methods", "Reusable delivery methods"),
    ("Deployments", "Release promotion history"),
    ("Dependencies", "Local A-BOM relationships"),
]
flyout = ''.join(f'<a class="nav-flyout-link {"active" if n=="Modules" else ""}">{ico()}<span class="nav-flyout-copy"><strong>{n}</strong><span>{d}</span></span><span>›</span></a>' for n,d in flyout_items)

sidebar = f'''
<aside class="sidebar preview-sidebar-r90">
  <div class="brand-row"><a class="brand"><span class="brand-mark">{ico()}</span><span class="brand-copy"><strong>CREED</strong></span></a></div>
  <nav class="nav nav-primary">
    <a class="nav-item">{ico()}<span>Overview</span></a><a class="nav-item">{ico()}<span>Issues</span></a><a class="nav-item">{ico()}<span>Change Radar</span></a><a class="nav-item">{ico()}<span>Knowledge</span></a><a class="nav-item">{ico()}<span>Recalls</span></a>
    <div class="nav-group nav-flyout-group contains-active"><button class="nav-item nav-group-toggle preview-registry-r90" aria-expanded="false">{ico()}<span>Registry</span><span class="nav-group-current">Modules</span><span class="nav-group-chevron">›</span></button>
      <div class="nav-flyout preview-flyout-r90" hidden><div class="nav-flyout-head"><div><strong>Registry</strong><span>7 workspaces</span></div></div><div class="nav-flyout-list">{flyout}</div></div>
    </div>
    <div class="nav-group nav-flyout-group"><button class="nav-item nav-group-toggle">{ico()}<span>Governance</span><span class="nav-group-chevron">›</span></button></div>
  </nav>
  <nav class="nav nav-utility"><a class="nav-item">{ico()}<span>AI Runtime</span></a></nav>
  <div class="sidebar-bottom"><button class="system-summary-btn ok"><span class="system-summary-icon">{ico()}</span><span class="system-summary-copy"><strong>System</strong><span>Healthy</span></span><span class="system-summary-chevron">›</span></button></div>
</aside>'''

rows = [
    ("Promise-to-Pay", "Collections", "Promise-to-Pay lifecycle, event processing and collection-state management.", "Active", "11111111-1111-4111-8111-111111111111"),
    ("Collections Case Management", "Collections", "Case queues, assignment and operational follow-up.", "Active", "22222222-2222-4222-8222-222222222222"),
    ("Legacy Recovery", "Legacy Collections", "Historical recovery capability retained for traceability.", "Inactive", "33333333-3333-4333-8333-333333333333"),
]
row_html = ""
for name, product, desc, status, mid in rows:
    active = status == "Active"
    row_html += f'''<div class="module-row-r90" role="row"><div class="module-identity-r90" role="cell" data-label="Module">{ico()}<strong>{name}</strong></div><div class="module-product-r90" role="cell" data-label="Product"><strong>{product}</strong>{'<span>Parent inactive</span>' if product=='Legacy Collections' else ''}</div><span class="module-description-cell-r90" role="cell" data-label="Description">{desc}</span><span class="module-status-r90 {'active' if active else 'inactive'}" role="cell" data-label="Status">{ico()}{status}</span><code role="cell" data-label="Module ID">{mid}</code><button class="module-status-action-r90">{ico()}<span>{'Deactivate' if active else 'Activate'}</span></button></div>'''

form = f'''<section class="module-create-r90 preview-create-r90" hidden><div class="module-create-head-r90"><div><h2>Register module</h2><p>Creates a product-scoped catalog record. Methods and implementations remain separate governed records.</p></div><button class="icon-btn">×</button></div><form class="module-create-form-r90"><label class="module-field-r90"><span>Product <b>Required</b></span><select><option>Collections</option></select><small>Only active products can receive new modules.</small></label><label class="module-field-r90"><span>Module name <b>Required</b></span><input value="Promise-to-Pay"><small>Use the stable capability name used in delivery and assurance records.</small></label><label class="module-field-r90 module-description-r90"><span>Description</span><textarea rows="3">Promise-to-Pay lifecycle, event processing and collection-state management.</textarea><small>Keep the description factual; method-level behavior belongs in the Method Registry.</small></label><label class="module-field-r90"><span>Catalog status</span><select><option>Active</option></select><small>Deactivation does not delete historical implementations, methods or ownership.</small></label><div class="module-create-actions-r90"><button class="ghost-btn">Cancel</button><button class="primary-btn">Add module</button></div></form></section>'''

main = f'''<main class="preview-main-r90"><header class="topbar"><nav class="crumb"><span>Registry</span><span>›</span><strong>Modules</strong></nav><div class="user-chip"><div class="user-copy"><strong>Assurance Lead</strong><span class="user-role-detail">Project Delivery</span></div><span class="avatar">{ico()}</span></div></header><div class="page module-registry-r90"><div class="title-row module-registry-title-r90"><div><h1>Modules</h1><p class="subtitle">Maintain product-scoped delivery capabilities used by implementations, methods and ownership.</p><div class="module-registry-summary-r90"><span><strong>3</strong> registered</span><span><strong>2</strong> active</span><span><strong>1</strong> inactive</span><span><strong>2</strong> products</span></div></div><button class="primary-btn preview-add-r90">+ Add module</button></div>{form}<section class="module-ledger-r90"><header class="module-ledger-head-r90"><div><h2>Module catalog</h2><span>3 of 3 visible</span></div><div class="module-ledger-controls-r90"><label class="module-search-r90">{ico()}<input placeholder="Search modules"></label><label class="module-filter-r90"><select><option>All products</option></select></label><label class="module-filter-r90"><select><option>All statuses</option></select></label></div></header><div class="module-table-r90" role="table"><div class="module-table-columns-r90" role="row"><span>Module</span><span>Product</span><span>Description</span><span>Status</span><span>Module ID</span><span></span></div>{row_html}</div></section></div></main>'''

html=f'''<!doctype html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><style>{css}
.preview-ico-r90{{width:15px;height:15px;display:inline-block;border:1.4px solid currentColor;border-radius:4px;box-sizing:border-box;opacity:.82}}
.preview-shell-r90{{min-height:100vh;display:grid;grid-template-columns:244px minmax(0,1fr);background:var(--creed-background)}}
.preview-sidebar-r90{{position:sticky;display:flex;top:0;height:100vh;overflow:visible}}
.preview-main-r90{{min-width:0}}.preview-main-r90 .page{{max-width:1420px;margin:0 auto}}.preview-add-r90{{white-space:nowrap}}
@media(max-width:760px){{.preview-shell-r90{{display:block}}.preview-sidebar-r90{{display:none!important}}.preview-main-r90 .page{{padding-inline:16px}}}}
</style></head><body><div class="preview-shell-r90">{sidebar}{main}</div><script>(()=>{{
const add=document.querySelector('.preview-add-r90'),form=document.querySelector('.preview-create-r90');add.addEventListener('click',()=>{{form.hidden=false;add.hidden=true;}});
const reg=document.querySelector('.preview-registry-r90'),fly=document.querySelector('.preview-flyout-r90');reg.addEventListener('click',()=>{{fly.hidden=!fly.hidden;reg.setAttribute('aria-expanded',String(!fly.hidden));}});
}})();</script></body></html>'''
out.parent.mkdir(parents=True, exist_ok=True)
out.write_text(html, encoding="utf-8")
print(out)
