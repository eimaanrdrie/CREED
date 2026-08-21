from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
css = (ROOT / 'frontend/app/globals.css').read_text(encoding='utf-8')
out = ROOT / 'scripts/fixtures/ui_r93_rev1_system_health_harness.html'
body = r'''
<div class="shell">
  <aside class="sidebar" id="desktop-sidebar">
    <div class="brand-row"><a class="brand"><span class="brand-mark">C</span><span class="brand-copy"><strong>CREED</strong></span></a></div>
    <nav class="nav nav-primary">
      <a class="nav-item"><span>O</span><span>Overview</span></a>
      <a class="nav-item"><span>I</span><span>Issues</span></a>
      <a class="nav-item"><span>R</span><span>Change Radar</span></a>
      <a class="nav-item"><span>K</span><span>Knowledge</span></a>
      <a class="nav-item"><span>C</span><span>Recalls</span></a>
      <div class="nav-group nav-flyout-group"><button class="nav-item nav-group-toggle"><span>R</span><span>Registry</span><span>›</span></button></div>
      <div class="nav-group nav-flyout-group"><button class="nav-item nav-group-toggle"><span>G</span><span>Governance</span><span>›</span></button></div>
    </nav>
    <nav class="nav nav-utility" aria-label="Runtime workspace">
      <a class="nav-item" id="primary-ai-runtime" href="/ai-runtime"><span>AI</span><span>AI Runtime</span></a>
    </nav>
    <div class="sidebar-bottom">
      <button class="system-summary-btn ok"><span>✓</span><span class="system-summary-copy"><strong>System</strong><span>Healthy</span></span><span>›</span></button>
      <div class="system-health-popover" id="system-health">
        <div class="system-health-head"><div><strong>System health</strong><span>Latest health check</span></div></div>
        <div class="system-health-list" role="status">
          <div class="system-health-row ok"><span>A</span><span>API</span><span class="system-health-state">Connected</span></div>
          <div class="system-health-row ok"><span>D</span><span>Database</span><span class="system-health-state">Connected</span></div>
          <div class="system-health-row ok"><span>Q</span><span>Qwen</span><span class="system-health-state">Connected</span></div>
          <div class="system-health-row ok"><span>K</span><span>Knowledge Source</span><span class="system-health-state">Connected</span></div>
        </div>
      </div>
    </div>
  </aside>
  <main class="main"><header class="topbar"><div class="crumb"><strong>Overview</strong></div></header><div class="page"><h1>R93 System Health harness</h1><p class="subtitle">System contains health only. AI Runtime remains the separate execution-proof destination.</p></div></main>
</div>
'''
out.write_text(f'<!doctype html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><style>{css}</style></head><body>{body}</body></html>', encoding='utf-8')
print(out)
