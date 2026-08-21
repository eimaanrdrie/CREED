from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
css = (ROOT / "frontend/app/globals.css").read_text(encoding="utf-8")
out = ROOT / "scripts/fixtures/ui_r82_rev1_method_registry_harness.html"

body = r'''
<div class="shell">
  <aside class="sidebar">
    <div class="brand-row"><a class="brand"><span class="brand-mark">C</span><span class="brand-copy"><strong>CREED</strong></span></a></div>
    <nav class="nav nav-primary">
      <a class="nav-item"><span>▦</span><span>Overview</span></a>
      <a class="nav-item"><span>!</span><span>Issues</span></a>
      <a class="nav-item"><span>◎</span><span>Change Radar</span></a>
      <a class="nav-item"><span>▣</span><span>Clients</span></a>
      <a class="nav-item"><span>▥</span><span>Implementations</span></a>
      <a class="nav-item active"><span>⑂</span><span>Methods</span></a>
      <a class="nav-item"><span>▤</span><span>Knowledge</span></a>
      <a class="nav-item"><span>↶</span><span>Recalls</span></a>
      <a class="nav-item"><span>◌</span><span>Audit</span></a>
      <a class="nav-item"><span>◇</span><span>AI Runtime</span></a>
    </nav>
    <div class="sidebar-bottom"><div class="system-signal-head"><span>System</span><span>Live</span></div><div class="system-status-list"><div class="system-status-row ok"><span>API</span><span class="system-state-value">Connected</span></div><div class="system-status-row ok"><span>DB</span><span class="system-state-value">Connected</span></div></div></div>
  </aside>
  <main class="main">
    <header class="topbar"><div class="crumb"><span>CREED</span><span class="crumb-segment">› <strong>Methods</strong></span></div><div class="user-chip"><div class="user-copy"><strong>Assurance Lead</strong><span>Project Delivery</span></div><span class="avatar">U</span></div></header>
    <div class="page method-registry-r82">
      <div class="title-row method-registry-title-r82"><div><h1>Methods</h1><p class="subtitle">Register reusable delivery methods and controlled versions without turning registration into adoption, approval or impact evidence.</p><div class="method-summary-r82"><span><strong>2</strong> methods</span><span><strong>3</strong> versions</span><span><strong>1</strong> approved</span><span><strong>2</strong> drafts</span></div></div></div>

      <section class="method-create-r82">
        <div class="method-create-head-r82"><div><h2>Register delivery method</h2><p>Creates the reusable method identity only. Version approval and implementation adoption remain separate governed actions.</p></div><button class="icon-btn">×</button></div>
        <form class="method-create-form-r82">
          <label class="method-field-r82"><span>Product <b>Required</b></span><select><option>Collections</option></select><small>Used to constrain the module choice.</small></label>
          <label class="method-field-r82"><span>Module <b>Required</b></span><select><option>Promise-to-Pay</option></select><small>The functional area that owns the reusable method.</small></label>
          <label class="method-field-r82 method-name-field-r82"><span>Method name <b>Required</b></span><input value="PTP Event Handling"><small>Stable name for the reusable delivery method.</small></label>
          <label class="method-field-r82 method-description-field-r82"><span>Description <b>Optional</b></span><input value="Reusable event-processing method for Promise-to-Pay"><small>Short operational purpose; do not encode a client-specific implementation here.</small></label>
          <div class="method-create-actions-r82"><button class="ghost-btn">Cancel</button><button class="primary-btn">＋ Register method</button></div>
        </form>
      </section>

      <section class="method-ledger-r82">
        <header class="method-ledger-head-r82"><div><h2>Delivery method ledger</h2><span>2 of 2 methods shown</span></div><div class="method-ledger-controls-r82"><label class="method-search-r82"><span>⌕</span><input placeholder="Search method, module or version"></label><label class="method-product-filter-r82"><select><option>All products</option></select></label></div></header>
        <div class="method-table-r82"><div class="method-table-columns-r82"><span>Method</span><span>Scope</span><span>Version history</span><span>Action</span></div>
          <div class="method-record-r82">
            <div class="method-row-r82"><div class="method-identity-r82"><span><strong>PTP Event Handling</strong><code>6de17c4b-a319-4b5e-8cb8-a7e14457de55</code><small>Reusable event-processing method for Promise-to-Pay.</small></span></div><div class="method-scope-r82" data-label="Scope"><strong>Promise-to-Pay</strong><small>Collections</small></div><div class="method-version-stack-r82" data-label="Version history"><div class="method-version-line-r82 approved"><code>PTP-EVENT-v1</code><span>✓ Approved</span></div><div class="method-version-line-r82 draft"><code>PTP-EVENT-v2</code><span>○ Draft</span></div></div><div class="method-row-action-r82" data-label="Action"><button class="secondary-btn compact">＋ Draft version</button></div></div>
          </div>
          <div class="method-record-r82">
            <div class="method-row-r82"><div class="method-identity-r82"><span><strong>Promise Evaluation Policy</strong><code>d649bf0b-ff61-4e52-9906-0fc9c5bb95cb</code><small>Reusable evaluation sequence for promise state changes.</small></span></div><div class="method-scope-r82" data-label="Scope"><strong>Promise-to-Pay</strong><small>Collections</small></div><div class="method-version-stack-r82" data-label="Version history"><div class="method-version-line-r82 draft"><code>PTP-POLICY-v1</code><span>○ Draft</span></div></div><div class="method-row-action-r82" data-label="Action"><button class="secondary-btn compact">× Close</button></div></div>
            <form class="method-version-create-r82"><div class="method-version-context-r82"><span>New draft for</span><strong>Promise Evaluation Policy</strong><small>Collections / Promise-to-Pay</small></div><label class="method-field-r82 method-version-label-r82"><span>Version label <b>Required</b></span><input value="PTP-POLICY-v2"></label><label class="method-field-r82 method-version-summary-r82"><span>Summary <b>Optional</b></span><input value="Clarifies duplicate-event evaluation order"></label><div class="method-version-actions-r82"><span>ⓘ New versions are always created as DRAFT. Approval and A-BOM adoption happen elsewhere.</span><button class="primary-btn">＋ Create draft</button></div></form>
          </div>
        </div>
      </section>
    </div>
  </main>
</div>
'''

html = f'<!doctype html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><style>{css}</style></head><body>{body}</body></html>'
out.write_text(html, encoding="utf-8")
print(out)
