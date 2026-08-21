from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
css=(ROOT/'frontend/app/globals.css').read_text(encoding='utf-8')
out=ROOT/'scripts/fixtures/ui_r92_rev1_flyout_harness.html'
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
      <div class="nav-group nav-flyout-group open contains-active" id="registry-group">
        <button class="nav-item nav-group-toggle active-parent" aria-expanded="true"><span>R</span><span>Registry</span><span class="nav-group-current">Methods</span><span>›</span></button>
        <span class="nav-flyout-bridge-r92" aria-hidden="true"></span>
        <div class="nav-flyout" id="registry-flyout">
          <div class="nav-flyout-head"><div><strong>Registry</strong><span>7 workspaces</span></div></div>
          <div class="nav-flyout-list">
            <a class="nav-flyout-link"><span class="nav-flyout-icon">P</span><span class="nav-flyout-copy"><strong>Products</strong><span>Delivery product catalog</span></span><span>›</span></a>
            <a class="nav-flyout-link"><span class="nav-flyout-icon">M</span><span class="nav-flyout-copy"><strong>Modules</strong><span>Product capability catalog</span></span><span>›</span></a>
            <a class="nav-flyout-link active"><span class="nav-flyout-icon">M</span><span class="nav-flyout-copy"><strong>Methods</strong><span>Reusable delivery methods</span></span><span>›</span></a>
          </div>
        </div>
      </div>
      <div class="nav-group nav-flyout-group"><button class="nav-item nav-group-toggle"><span>G</span><span>Governance</span><span>›</span></button></div>
    </nav>
    <nav class="nav nav-utility"><a class="nav-item"><span>AI</span><span>AI Runtime</span></a></nav>
    <div class="sidebar-bottom"><button class="system-summary-btn ok"><span>✓</span><span class="system-summary-copy"><strong>System</strong><span>Healthy</span></span><span>›</span></button></div>
  </aside>
  <main class="main"><header class="topbar"><div class="crumb"><strong>Methods</strong></div></header><div class="page"><h1>Flyout interaction harness</h1><p class="subtitle">Registry flyout remains visually bounded while the transparent bridge occupies only the rail-to-panel gap.</p></div></main>
</div>
'''
out.write_text(f'<!doctype html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><style>{css}</style></head><body>{body}</body></html>',encoding='utf-8')
print(out)
