from pathlib import Path
import os
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[1]
HTML=(ROOT/'scripts/fixtures/ui_r91_rev1_method_baseline_harness.html').resolve()
OUT=ROOT/'scripts/fixtures'
widths=[1440,1100,900,760,560,390]
results=[]
with sync_playwright() as p:
    default=p.chromium.executable_path
    executable=default if os.path.exists(default) else ('/usr/bin/chromium' if os.path.exists('/usr/bin/chromium') else None)
    kwargs={'headless':True,'args':['--no-sandbox']}
    if executable: kwargs['executable_path']=executable
    browser=p.chromium.launch(**kwargs)
    page=browser.new_page(viewport={'width':1440,'height':1000})
    html=HTML.read_text(encoding='utf-8')
    for width in widths:
        height=1000 if width>=900 else 920
        page.set_viewport_size({'width':width,'height':height})
        page.set_content(html,wait_until='load')
        overflow=page.evaluate('document.documentElement.scrollWidth > document.documentElement.clientWidth')
        form_overflow=page.evaluate("document.querySelector('.method-baseline-approval-r91').scrollWidth > document.querySelector('.method-baseline-approval-r91').clientWidth + 1")
        row_overflow=page.evaluate("Array.from(document.querySelectorAll('.method-row-r82')).some(el => el.scrollWidth > el.clientWidth + 1)")
        results.append((width,overflow,form_overflow,row_overflow))
        if width in (1440,390):
            page.screenshot(path=str(OUT/f'ui_r91_rev1_method_baseline_{width}.png'),full_page=True)
    browser.close()
for item in results: print(item)
if any(any(item[1:]) for item in results): raise SystemExit('UI-R91 browser sweep failed')
print('UI-R91 REV1 browser sweep PASS')
