from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
css = (ROOT / "frontend/app/globals.css").read_text(encoding="utf-8").replace('@import "tailwindcss";','',1)
out = ROOT / "scripts/fixtures/ui_r89_rev1_products_harness.html"

def ico():
    return '<span class="preview-ico-r89" aria-hidden="true"></span>'

sidebar = f'''
<aside class="sidebar preview-sidebar-r89">
  <div class="brand-row"><a class="brand"><span class="brand-mark">{ico()}</span><span class="brand-copy"><strong>CREED</strong></span></a></div>
  <nav class="nav nav-primary">
    <a class="nav-item">{ico()}<span>Overview</span></a>
    <a class="nav-item">{ico()}<span>Issues</span></a>
    <a class="nav-item">{ico()}<span>Change Radar</span></a>
    <a class="nav-item">{ico()}<span>Knowledge</span></a>
    <a class="nav-item">{ico()}<span>Recalls</span></a>
    <div class="nav-group nav-flyout-group contains-active">
      <button class="nav-item nav-group-toggle active-parent" aria-expanded="false">{ico()}<span>Registry</span><span class="nav-group-current">Products</span><span class="nav-group-chevron">›</span></button>
    </div>
    <div class="nav-group nav-flyout-group">
      <button class="nav-item nav-group-toggle" aria-expanded="false">{ico()}<span>Governance</span><span class="nav-group-chevron">›</span></button>
    </div>
  </nav>
  <nav class="nav nav-utility"><a class="nav-item">{ico()}<span>AI Runtime</span></a></nav>
  <div class="sidebar-bottom"><button class="system-summary-btn ok"><span class="system-summary-icon">{ico()}</span><span class="system-summary-copy"><strong>System</strong><span>Healthy</span></span><span class="system-summary-chevron">›</span></button></div>
</aside>
'''

rows = [
    ("Collections", "Collections platform covering repayment, recovery and customer commitment workflows.", "Active", "11111111-1111-4111-8111-111111111111"),
    ("Loan Origination", "Origination journeys, application capture, decisioning and onboarding.", "Active", "22222222-2222-4222-8222-222222222222"),
    ("Legacy Collections", "Retained catalog entry for historical implementation traceability.", "Inactive", "33333333-3333-4333-8333-333333333333"),
]
row_html = ""
for name, desc, status, pid in rows:
    active = status == "Active"
    row_html += f'''
    <div class="product-row-r89" role="row">
      <div class="product-identity-r89" role="cell" data-label="Product">{ico()}<strong>{name}</strong></div>
      <span class="product-description-cell-r89" role="cell" data-label="Description">{desc}</span>
      <span class="product-status-r89 {'active' if active else 'inactive'}" role="cell" data-label="Status">{ico()}{status}</span>
      <code role="cell" data-label="Product ID">{pid}</code>
      <button class="product-status-action-r89">{ico()}<span>{'Deactivate' if active else 'Activate'}</span></button>
    </div>'''

form = '''
<section class="product-create-r89 preview-create-r89" hidden>
  <div class="product-create-head-r89"><div><h2>Register product</h2><p>Creates a persistent catalog record. Modules are registered separately and are never created implicitly.</p></div><button class="icon-btn">×</button></div>
  <form class="product-create-form-r89">
    <label class="product-field-r89"><span>Product name <b>Required</b></span><input value="Collections"><small>Use the stable product name that should appear across delivery and assurance records.</small></label>
    <label class="product-field-r89 product-description-r89"><span>Description</span><textarea rows="3">Collections platform covering repayment, recovery and customer commitment workflows.</textarea><small>Keep this factual. Modules and methods provide the more specific implementation detail.</small></label>
    <label class="product-field-r89"><span>Catalog status</span><select><option>Active</option></select><small>Status is catalog metadata. Existing records are not deleted when a product becomes inactive.</small></label>
    <div class="product-create-actions-r89"><button class="ghost-btn">Cancel</button><button class="primary-btn">Add product</button></div>
  </form>
</section>
'''

main = f'''
<main class="preview-main-r89">
  <header class="topbar"><nav class="crumb"><span>Registry</span><span>›</span><strong>Products</strong></nav><div class="user-chip"><div class="user-copy"><strong>Assurance Lead</strong><span class="user-role-detail">Project Delivery</span></div><span class="avatar">{ico()}</span></div></header>
  <div class="page product-registry-r89">
    <div class="title-row product-registry-title-r89">
      <div><h1>Products</h1><p class="subtitle">Maintain the delivery product catalog used by modules, implementations, methods and ownership.</p><div class="product-registry-summary-r89"><span><strong>3</strong> registered</span><span><strong>2</strong> active</span><span><strong>1</strong> inactive</span></div></div>
      <button class="primary-btn preview-add-r89">+ Add product</button>
    </div>
    {form}
    <section class="product-ledger-r89">
      <header class="product-ledger-head-r89"><div><h2>Product catalog</h2><span>3 of 3 visible</span></div><div class="product-ledger-controls-r89"><label class="product-search-r89">{ico()}<input placeholder="Search products"></label><label class="product-status-filter-r89"><select><option>All statuses</option></select></label></div></header>
      <div class="product-table-r89" role="table">
        <div class="product-table-columns-r89" role="row"><span>Product</span><span>Description</span><span>Status</span><span>Product ID</span><span></span></div>
        {row_html}
      </div>
    </section>
  </div>
</main>
'''

html=f'''<!doctype html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><style>{css}
.preview-ico-r89{{width:15px;height:15px;display:inline-block;border:1.4px solid currentColor;border-radius:4px;box-sizing:border-box;opacity:.82}}
.preview-shell-r89{{min-height:100vh;display:grid;grid-template-columns:244px minmax(0,1fr);background:var(--creed-background)}}
.preview-sidebar-r89{{position:sticky;display:flex;top:0;height:100vh}}
.preview-main-r89{{min-width:0}}
.preview-main-r89 .page{{max-width:1420px;margin:0 auto}}
.preview-add-r89{{white-space:nowrap}}
@media(max-width:760px){{.preview-shell-r89{{display:block}}.preview-sidebar-r89{{display:none!important}}.preview-main-r89 .page{{padding-inline:16px}}}}
</style></head><body><div class="preview-shell-r89">{sidebar}{main}</div><script>
const add=document.querySelector('.preview-add-r89');const form=document.querySelector('.preview-create-r89');
add.addEventListener('click',()=>{{form.hidden=false;add.hidden=true;}});
</script></body></html>'''
out.write_text(html, encoding="utf-8")
print(out)
