from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
css=(ROOT/'frontend/app/globals.css').read_text(encoding='utf-8')
out=ROOT/'scripts/fixtures/ui_r91_rev1_method_baseline_harness.html'
body=r'''
<div class="shell">
  <aside class="sidebar">
    <div class="brand-row"><a class="brand"><span class="brand-mark">C</span><span class="brand-copy"><strong>CREED</strong></span></a></div>
    <nav class="nav nav-primary">
      <a class="nav-item"><span>O</span><span>Overview</span></a>
      <a class="nav-item"><span>I</span><span>Issues</span></a>
      <a class="nav-item"><span>R</span><span>Change Radar</span></a>
      <a class="nav-item"><span>K</span><span>Knowledge</span></a>
      <a class="nav-item"><span>C</span><span>Recalls</span></a>
      <a class="nav-item active"><span>R</span><span>Registry</span></a>
      <a class="nav-item"><span>G</span><span>Governance</span></a>
    </nav>
    <div class="sidebar-bottom"><a class="nav-item"><span>AI</span><span>AI Runtime</span></a><div class="system-signal-head"><span>System</span><span>Healthy</span></div></div>
  </aside>
  <main class="main">
    <header class="topbar"><div class="crumb"><span>Registry</span><span class="crumb-segment">› <strong>Methods</strong></span></div><div class="user-chip"><div class="user-copy"><strong>Assurance Lead</strong></div><span class="avatar">U</span></div></header>
    <div class="page method-registry-r82">
      <div class="title-row method-registry-title-r82"><div><h1>Methods</h1><p class="subtitle">Register reusable delivery methods, controlled versions and the one-time governed baseline that anchors later learning and recall.</p><div class="method-summary-r82"><span><strong>2</strong> methods</span><span><strong>2</strong> versions</span><span><strong>1</strong> approved</span><span><strong>1</strong> drafts</span></div></div><button class="primary-btn">+ Add method</button></div>

      <section class="method-ledger-r82">
        <header class="method-ledger-head-r82"><div><h2>Delivery method ledger</h2><span>2 of 2 methods shown</span></div><div class="method-ledger-controls-r82"><label class="method-search-r82"><input placeholder="Search method, module or version"></label><label class="method-product-filter-r82"><select><option>All products</option></select></label></div></header>
        <div class="method-table-r82">
          <div class="method-table-columns-r82"><span>Method</span><span>Scope</span><span>Version history</span><span>Action</span></div>
          <div class="method-record-r82">
            <div class="method-row-r82">
              <div class="method-identity-r82"><span><strong>PTP Event Handling</strong><code>33333333-3333-4333-8333-333333333333</code><small>Reusable event-processing method for Promise-to-Pay.</small></span></div>
              <div class="method-scope-r82" data-label="Scope"><strong>Promise-to-Pay</strong><small>Collections</small></div>
              <div class="method-version-stack-r82" data-label="Version history"><div class="method-version-line-r82 draft"><code>PTP-EVENT-v1</code><span>Draft</span><button class="method-baseline-trigger-r91">Approve baseline</button></div></div>
              <div class="method-row-action-r82" data-label="Action"><button class="secondary-btn compact">+ Draft version</button></div>
            </div>
            <form class="method-baseline-approval-r91">
              <div class="method-version-context-r82"><span>Initial governed baseline</span><strong>PTP-EVENT-v1</strong><small>PTP Event Handling / Collections / Promise-to-Pay</small></div>
              <label class="method-field-r82"><span>Approving authority <b>Required</b></span><select><option>Aisha Rahman — Transformation Assurance Lead</option></select><small>Active principals with Learning approval are eligible for initial method governance.</small></label>
              <label class="method-field-r82 method-baseline-reason-r91"><span>Approval rationale <b>Required</b></span><textarea>Initial approved baseline for existing Promise-to-Pay implementations.</textarea><small>This establishes the first approved baseline only. It does not adopt the version into any implementation.</small></label>
              <div class="method-baseline-actions-r91"><span>This one-time setup action is blocked after a baseline has been approved or revoked. Later versions must use the governed learning workflow.</span><div><button class="ghost-btn">Cancel</button><button class="primary-btn">Approve baseline</button></div></div>
            </form>
          </div>
          <div class="method-record-r82">
            <div class="method-row-r82">
              <div class="method-identity-r82"><span><strong>Promise Evaluation Policy</strong><code>d649bf0b-ff61-4e52-9906-0fc9c5bb95cb</code><small>Reusable evaluation sequence for promise state changes.</small></span></div>
              <div class="method-scope-r82" data-label="Scope"><strong>Promise-to-Pay</strong><small>Collections</small></div>
              <div class="method-version-stack-r82" data-label="Version history"><div class="method-version-line-r82 approved"><code>PTP-POLICY-v1</code><span>Approved</span></div></div>
              <div class="method-row-action-r82" data-label="Action"><button class="secondary-btn compact">+ Draft version</button></div>
            </div>
          </div>
        </div>
      </section>
    </div>
  </main>
</div>
'''
out.write_text(f'<!doctype html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><style>{css}</style></head><body>{body}</body></html>',encoding='utf-8')
print(out)
