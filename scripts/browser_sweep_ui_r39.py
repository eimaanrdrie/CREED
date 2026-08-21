"""UI-R39 full-shell Knowledge proof overflow sweep using actual CREED CSS."""
from pathlib import Path
import re, shutil, sys
ROOT=Path(__file__).resolve().parents[1]
CSS=(ROOT/'frontend/app/globals.css').read_text(encoding='utf-8')
HARNESS=(ROOT/'scripts/fixtures/ui_r39_knowledge_shell_harness.html').read_text(encoding='utf-8')
try:
    from playwright.sync_api import sync_playwright
except ImportError:
    print('SKIP: Python Playwright is not installed'); sys.exit(2)
chromium=shutil.which('chromium') or shutil.which('chromium-browser') or shutil.which('google-chrome')
if not chromium:
    print('SKIP: Chromium executable not found'); sys.exit(2)
css=re.sub(r'^@import\s+"tailwindcss";\s*','',CSS)
html=re.sub(r'<link rel="stylesheet"[^>]*>','<style>'+css+'</style>',HARNESS,count=1)
widths=[760,820,900,1024,1180,1280,1366,1440,1536,1600,1920]
fail=[]
with sync_playwright() as p:
    browser=p.chromium.launch(executable_path=chromium,headless=True,args=['--no-sandbox','--disable-dev-shm-usage','--disable-gpu'])
    page=browser.new_page(viewport={'width':1536,'height':900})
    for width in widths:
        page.set_viewport_size({'width':width,'height':900})
        page.set_content(html,wait_until='load',timeout=20_000)
        page.wait_for_timeout(50)
        data=page.evaluate('''() => {
          const root=document.querySelector('.knowledge-proof-stack-r27');
          const nodes=[document.documentElement,document.body,document.querySelector('.main'),document.querySelector('.page'),root,...root.querySelectorAll('.progressive-disclosure,.progressive-disclosure-body,.registry-min-r27,.registry-search-r06,.registry-ledger-r06,.registry-row-r06,.knowledge-provenance-min-r27,.knowledge-provenance-min-r27>div')];
          return nodes.filter(Boolean).map(el=>({name:el.className||el.tagName, sw:el.scrollWidth,cw:el.clientWidth})).filter(x=>x.sw>x.cw+1);
        }''')
        if data: fail.append({'width':width,'overflow':data})
    browser.close()
if fail:
    import json; print(json.dumps(fail,indent=2)); sys.exit(1)
print('UI-R39 full-shell Knowledge overflow sweep: PASS')
