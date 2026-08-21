"""UI-R47 Audit deep-proof full-shell overflow sweep using actual CREED CSS."""
from pathlib import Path
import re, shutil, sys, json
ROOT=Path(__file__).resolve().parents[1]
CSS=(ROOT/'frontend/app/globals.css').read_text(encoding='utf-8')
HARNESS=(ROOT/'scripts/fixtures/ui_r47_audit_shell_harness.html').read_text(encoding='utf-8')
try:
    from playwright.sync_api import sync_playwright
except ImportError:
    print('SKIP: Python Playwright is not installed'); sys.exit(2)
chromium=shutil.which('chromium') or shutil.which('chromium-browser') or shutil.which('google-chrome')
if not chromium:
    print('SKIP: Chromium executable not found'); sys.exit(2)
css=re.sub(r'^@import\s+"tailwindcss";\s*','',CSS)
html=re.sub(r'<link rel="stylesheet"[^>]*>','<style>'+css+'</style>',HARNESS,count=1)
widths=[360,390,430,620,760,900,1024,1180,1280,1366,1440,1600,1920]
fail=[]
with sync_playwright() as p:
    browser=p.chromium.launch(executable_path=chromium,headless=True,args=['--no-sandbox','--disable-dev-shm-usage','--disable-gpu'])
    page=browser.new_page(viewport={'width':1440,'height':950})
    for width in widths:
        page.set_viewport_size({'width':width,'height':950})
        page.set_content(html,wait_until='load',timeout=20_000)
        page.wait_for_timeout(30)
        data=page.evaluate('''() => {
          const root=document.querySelector('.audit-r29');
          const selectors='.audit-deep-proof-r47,.progressive-disclosure,.progressive-disclosure-body,.audit-deep-grid-r47,.audit-deep-group-r47,.audit-agent-row-r47,.audit-qwen-row-r47,.audit-evidence-row-r47,.audit-impact-row-r47,.audit-human-row-r47,.audit-governance-row-r47';
          const nodes=[document.documentElement,document.body,document.querySelector('.main'),root,...root.querySelectorAll(selectors)];
          return nodes.filter(Boolean).map(el=>({name:typeof el.className==='string'?el.className:el.tagName,sw:el.scrollWidth,cw:el.clientWidth})).filter(x=>x.sw>x.cw+1);
        }''')
        if data: fail.append({'width':width,'overflow':data})
    page.set_viewport_size({'width':1440,'height':950}); page.set_content(html,wait_until='load'); page.screenshot(path=str(ROOT/'scripts/fixtures/ui_r47_audit_preview.png'),full_page=True)
    browser.close()
if fail:
    print(json.dumps(fail,indent=2)); sys.exit(1)
print('UI-R47 full-shell Audit deep-proof overflow sweep: PASS')
