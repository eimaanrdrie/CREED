from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
css = (ROOT / "frontend/app/globals.css").read_text(encoding="utf-8").replace('@import "tailwindcss";','',1)
out = ROOT / "scripts/fixtures/ui_r88_rev1_sidebar_harness.html"

def icon():
    return '<span class="preview-icon-r88" aria-hidden="true"></span>'

def link(label, active=False, child=False):
    classes = ['nav-item']
    if child: classes.append('nav-item-child')
    if active: classes.append('active')
    return f'<a class="{" ".join(classes)}" href="#">{icon()}<span>{label}</span></a>'

def group(label, children, gid):
    child_html = ''.join(link(item, child=True) for item in children)
    return f'''<div class="nav-group" data-preview-group="{gid}"><button class="nav-item nav-group-toggle" type="button" aria-expanded="false" aria-controls="{gid}-panel">{icon()}<span>{label}</span><span class="preview-chevron-r88 nav-group-chevron" aria-hidden="true">›</span></button><div class="nav-group-panel" id="{gid}-panel" hidden><div class="nav-group-inner" role="group" aria-label="{label} workspaces">{child_html}</div></div></div>'''

sidebar_html = f'''<aside class="sidebar preview-sidebar-r88" aria-label="Primary navigation"><div class="brand-row"><a class="brand" href="#"><span class="brand-mark">{icon()}</span><span class="brand-copy"><strong>CREED</strong></span></a></div><nav class="nav nav-primary">{link('Overview', True)}{link('Issues')}{link('Change Radar')}{link('Knowledge')}{link('Recalls')}{group('Registry',['Clients','Implementations','Methods','Deployments','Dependencies'],'registry')}{group('Governance',['Authority','Ownership','Audit'],'governance')}</nav><nav class="nav nav-utility">{link('AI Runtime')}</nav><div class="sidebar-bottom"><div class="system-signal-head"><span>System</span><span>Live</span></div><div class="system-status-list"><div class="system-status-row ok"><span class="system-service-icon">{icon()}</span><span class="system-service-name">API</span><span class="system-state-value">Connected</span></div><div class="system-status-row ok"><span class="system-service-icon">{icon()}</span><span class="system-service-name">DB</span><span class="system-state-value">Connected</span></div><div class="system-status-row ok"><span class="system-service-icon">{icon()}</span><span class="system-service-name">Qwen</span><span class="system-state-value">Connected</span></div></div></div></aside>'''

html = f'''<!doctype html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><style>{css}
.preview-icon-r88{{width:16px;height:16px;display:inline-block;border:1.5px solid currentColor;border-radius:4px;opacity:.88;box-sizing:border-box}}
.brand-mark .preview-icon-r88{{width:17px;height:17px;border-color:currentColor}}
.preview-chevron-r88{{font-size:18px;line-height:1;display:inline-grid;place-items:center}}
.preview-shell-r88{{min-height:100vh;display:grid;grid-template-columns:244px minmax(0,1fr);background:var(--creed-background)}}
.preview-shell-r88>.preview-sidebar-r88{{position:sticky;display:flex;top:0;height:100vh}}
.preview-main-r88{{min-width:0;background:var(--creed-background)}}
.preview-topbar-r88{{height:68px;border-bottom:1px solid var(--creed-hairline);display:flex;align-items:center;justify-content:space-between;padding:0 30px;color:var(--creed-secondary);font-size:13px}}
.preview-role-r88{{display:flex;align-items:center;gap:12px}}.preview-role-r88 b{{color:var(--creed-secondary)}}
.preview-content-r88{{padding:54px 38px 48px;max-width:1420px;margin:0 auto}}
.preview-content-r88 h1{{font-size:54px;line-height:1.04;max-width:660px;margin:0;color:var(--creed-off-white);font-weight:620}}
.preview-content-r88 p{{margin:14px 0 28px;color:var(--creed-secondary);font-size:15px}}
.preview-rule-r88{{height:1px;background:var(--creed-hairline);margin:0 0 22px}}
.preview-metrics-r88{{display:grid;grid-template-columns:repeat(3,1fr);border:1px solid var(--creed-hairline);border-radius:7px;overflow:hidden}}
.preview-metric-r88{{min-height:132px;padding:22px;border-right:1px solid var(--creed-hairline)}}.preview-metric-r88:last-child{{border-right:0}}.preview-metric-r88 span{{font:650 11px/1.2 ui-monospace,monospace;letter-spacing:.08em;text-transform:uppercase;color:var(--creed-muted)}}.preview-metric-r88 strong{{display:block;margin-top:22px;font-size:38px;color:var(--creed-off-white)}}
.preview-path-r88{{margin-top:18px;border:1px solid var(--creed-hairline);border-radius:7px;padding:22px;min-height:180px}}.preview-path-r88 h2{{margin:0;color:var(--creed-off-white);font-size:17px}}.preview-path-steps-r88{{display:grid;grid-template-columns:repeat(5,1fr);gap:1px;margin-top:24px;background:var(--creed-hairline)}}.preview-path-steps-r88 span{{background:var(--creed-surface);padding:24px 16px;color:var(--creed-secondary);font-size:12px}}
.preview-mobile-layer-r88{{display:none}}
@media(max-width:760px){{.preview-shell-r88{{display:block}}.preview-shell-r88>.preview-sidebar-r88{{display:none!important}}.preview-main-r88{{min-height:100vh}}.preview-content-r88{{padding:28px 16px}}.preview-content-r88 h1{{font-size:34px}}.preview-metrics-r88{{grid-template-columns:1fr}}.preview-metric-r88{{border-right:0;border-bottom:1px solid var(--creed-hairline)}}.preview-path-steps-r88{{grid-template-columns:1fr}}.preview-mobile-layer-r88{{display:block;position:fixed;inset:0;background:color-mix(in oklab,var(--creed-background) 72%,transparent);z-index:200}}.preview-mobile-layer-r88>.sidebar-mobile{{display:flex!important;position:absolute;inset:0 auto 0 0;height:100%;width:min(88vw,330px);box-shadow:18px 0 60px rgba(0,0,0,.32)}}}}
</style></head><body><div class="preview-shell-r88">{sidebar_html}<main class="preview-main-r88"><div class="preview-topbar-r88"><span>Overview</span><span class="preview-role-r88"><b>Assurance Lead</b>{icon()}</span></div><section class="preview-content-r88"><h1>See what needs action. Prove why.</h1><p>Issue → evidence → impact → human → recall.</p><div class="preview-rule-r88"></div><div class="preview-metrics-r88"><div class="preview-metric-r88"><span>Human decisions</span><strong>0</strong></div><div class="preview-metric-r88"><span>Active recalls</span><strong>0</strong></div><div class="preview-metric-r88"><span>High priority</span><strong>0</strong></div></div><div class="preview-path-r88"><h2>Assurance path</h2><div class="preview-path-steps-r88"><span>Issues</span><span>Evidence</span><span>Impact</span><span>Human</span><span>Recall</span></div></div></section></main></div><div class="preview-mobile-layer-r88">{sidebar_html.replace('preview-sidebar-r88','preview-sidebar-r88 sidebar-mobile')}</div><script>
document.querySelectorAll('.nav-group-toggle').forEach((button)=>button.addEventListener('click',()=>{{const group=button.closest('.nav-group');const panel=group.querySelector('.nav-group-panel');const open=button.getAttribute('aria-expanded')==='true';button.setAttribute('aria-expanded',String(!open));panel.hidden=open;group.classList.toggle('open',!open);}}));
</script></body></html>'''
out.write_text(html, encoding="utf-8")
print(out)
