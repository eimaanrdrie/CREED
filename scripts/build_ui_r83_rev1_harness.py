from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
css = (ROOT / "frontend/app/globals.css").read_text(encoding="utf-8")
out = ROOT / "scripts/fixtures/ui_r83_rev1_dependency_registry_harness.html"

body = r'''
<div class="shell">
  <aside class="sidebar">
    <div class="brand-row"><a class="brand"><span class="brand-mark">C</span><span class="brand-copy"><strong>CREED</strong></span></a></div>
    <nav class="nav nav-primary">
      <a class="nav-item"><span>▦</span><span>Overview</span></a><a class="nav-item"><span>!</span><span>Issues</span></a><a class="nav-item"><span>◎</span><span>Change Radar</span></a><a class="nav-item"><span>▣</span><span>Clients</span></a><a class="nav-item"><span>▥</span><span>Implementations</span></a><a class="nav-item"><span>⑂</span><span>Methods</span></a><a class="nav-item active"><span>⌘</span><span>Dependencies</span></a><a class="nav-item"><span>▤</span><span>Knowledge</span></a><a class="nav-item"><span>↶</span><span>Recalls</span></a><a class="nav-item"><span>◌</span><span>Audit</span></a><a class="nav-item"><span>◇</span><span>AI Runtime</span></a>
    </nav>
    <div class="sidebar-bottom"><div class="system-signal-head"><span>System</span><span>Live</span></div><div class="system-status-list"><div class="system-status-row ok"><span>API</span><span class="system-state-value">Connected</span></div><div class="system-status-row ok"><span>DB</span><span class="system-state-value">Connected</span></div></div></div>
  </aside>
  <main class="main">
    <header class="topbar"><div class="crumb"><span>CREED</span><span class="crumb-segment">› <strong>Dependencies</strong></span></div><div class="user-chip"><div class="user-copy"><strong>Assurance Lead</strong><span>Project Delivery</span></div><span class="avatar">U</span></div></header>
    <div class="page dependency-registry-r83">
      <div class="title-row dependency-registry-title-r83"><div><h1>Dependencies</h1><p class="subtitle">Maintain the Local A-BOM relationships that connect a client implementation to the method version it actually uses, with evidence attached to every new registration.</p><div class="dependency-summary-r83"><span><strong>3</strong> relationships</span><span><strong>3</strong> implementations linked</span><span><strong>1</strong> method version in use</span><span><strong>3</strong> evidence-backed</span></div></div><button class="primary-btn">＋ Register dependency</button></div>

      <section class="dependency-create-r83">
        <div class="dependency-create-head-r83"><div><h2>Register implementation dependency</h2><p>This writes one explicit <code>USES_METHOD_VERSION</code> edge. It does not approve the method, declare an implementation affected, or create a governance adoption receipt.</p></div><button class="icon-btn">×</button></div>
        <form class="dependency-create-form-r83">
          <label class="dependency-field-r83"><span>Implementation <b>Required</b></span><select><option>Atlas Bank — Atlas PTP Implementation · R1</option></select><small>The deployed client-specific solution that owns this dependency.</small></label>
          <label class="dependency-field-r83"><span>Method version <b>Required</b></span><select><option>PTP Event Handling — PTP-EVENT-v1 · APPROVED</option></select><small>Only method versions from the same module are available.</small></label>
          <label class="dependency-field-r83 dependency-evidence-field-r83"><span>Supporting evidence <b>Required</b></span><select><option>CFG-ATLAS-PTP-01 · CONFIGURATION · 1.0</option></select><small>Use a configuration, release or design record that supports the dependency claim.</small></label>
          <div class="dependency-create-context-r83"><span>ⓘ</span><span>A-BOM registration records current implementation usage only. Impact, Human Decision, adoption and recall remain separate governed workflows.</span></div>
          <div class="dependency-create-actions-r83"><button class="ghost-btn">Cancel</button><button class="primary-btn">⌁ Register dependency</button></div>
        </form>
      </section>

      <section class="dependency-ledger-r83">
        <header class="dependency-ledger-head-r83"><div><h2>Local A-BOM ledger</h2><span>3 of 3 relationships shown</span></div><div class="dependency-ledger-controls-r83"><label class="dependency-search-r83"><span>⌕</span><input placeholder="Search client, implementation or method"></label><label class="dependency-client-filter-r83"><select><option>All clients</option></select></label></div></header>
        <div class="dependency-table-r83"><div class="dependency-table-columns-r83"><span>Implementation</span><span>Uses method version</span><span>Supporting evidence</span><span>Action</span></div>
          <div class="dependency-record-r83"><div class="dependency-row-r83"><div class="dependency-implementation-r83"><span class="dependency-node-icon-r83">⌘</span><span><strong>Atlas PTP Implementation</strong><small>Atlas Bank · Collections / Promise-to-Pay</small><code>R1 · 13af8a24-af25-88f3-4e06-1d0b2d87a1bb</code></span></div><div class="dependency-method-r83" data-label="Uses method version"><strong>PTP Event Handling</strong><code>PTP-EVENT-v1</code><span class="approved">Approved</span></div><div class="dependency-evidence-r83" data-label="Supporting evidence"><span>✓</span><span><strong>CFG-ATLAS-PTP-01</strong><small>CONFIGURATION · 1.0</small><code>35a57ce6a87b…b1a745ffb3f3</code></span></div><div class="dependency-action-r83" data-label="Action"><button class="dependency-remove-trigger-r83">× Remove</button></div></div></div>
          <div class="dependency-record-r83"><div class="dependency-row-r83"><div class="dependency-implementation-r83"><span class="dependency-node-icon-r83">⌘</span><span><strong>Meridian PTP Implementation With An Intentionally Long Name</strong><small>Meridian Bank · Collections / Promise-to-Pay</small><code>R1 · f9ee7bd5-44d0-d7c9-e7d7-908845e687db</code></span></div><div class="dependency-method-r83" data-label="Uses method version"><strong>PTP Event Handling</strong><code>PTP-EVENT-v1</code><span class="approved">Approved</span></div><div class="dependency-evidence-r83" data-label="Supporting evidence"><span>✓</span><span><strong>CFG-MERIDIAN-PTP-04</strong><small>CONFIGURATION · 1.0</small><code>642c4eb225b5…160961a4a57f</code></span></div><div class="dependency-action-r83" data-label="Action"><button class="dependency-remove-trigger-r83">× Remove</button></div></div>
            <form class="dependency-remove-r83"><div class="dependency-remove-context-r83"><span>!</span><span><strong>Remove current A-BOM relationship?</strong><small>This changes impact and recall routing for Meridian PTP Implementation. The removal action is retained in Audit.</small></span></div><label><span>Reason <b>Required</b></span><textarea>Configuration was replaced by a later release record.</textarea></label><div class="dependency-remove-actions-r83"><button class="ghost-btn">Cancel</button><button class="dependency-remove-confirm-r83">× Remove dependency</button></div></form>
          </div>
          <div class="dependency-record-r83"><div class="dependency-row-r83"><div class="dependency-implementation-r83"><span class="dependency-node-icon-r83">⌘</span><span><strong>Nova PTP Implementation</strong><small>Nova Finance · Collections / Promise-to-Pay</small><code>R1 · 5dde1cd7-cee4-8cd2-4895-a155a67b7a56</code></span></div><div class="dependency-method-r83" data-label="Uses method version"><strong>PTP Event Handling</strong><code>PTP-EVENT-v1</code><span class="approved">Approved</span></div><div class="dependency-evidence-r83" data-label="Supporting evidence"><span>✓</span><span><strong>CFG-NOVA-PTP-08</strong><small>CONFIGURATION · 1.0</small><code>d5ccd1561f9c…85ec421878cf</code></span></div><div class="dependency-action-r83" data-label="Action"><button class="dependency-remove-trigger-r83">× Remove</button></div></div></div>
        </div>
      </section>
    </div>
  </main>
</div>
'''

html = f'<!doctype html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><style>{css}</style></head><body>{body}</body></html>'
out.write_text(html, encoding="utf-8")
print(out)
