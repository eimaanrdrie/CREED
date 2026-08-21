from pathlib import Path
import os
from playwright.sync_api import sync_playwright

ROOT=Path(__file__).resolve().parents[1]
HTML=(ROOT/'scripts/fixtures/ui_r85_rev1_authority_enforcement_harness.html').resolve()
OUT=ROOT/'scripts/fixtures'
widths=[1440,1100,900,760,560,390]
results=[]
with sync_playwright() as p:
    default_exe=p.chromium.executable_path
    executable=default_exe if os.path.exists(default_exe) else ("/usr/bin/chromium" if os.path.exists("/usr/bin/chromium") else None)
    launch_kwargs={"headless":True,"args":["--no-sandbox"]}
    if executable: launch_kwargs["executable_path"]=executable
    browser=p.chromium.launch(**launch_kwargs)
    page=browser.new_page(viewport={"width":1440,"height":1100})
    for width in widths:
        page.set_viewport_size({"width":width,"height":1100})
        page.set_content(HTML.read_text(encoding="utf-8"),wait_until="load")
        overflow=page.evaluate("document.documentElement.scrollWidth > document.documentElement.clientWidth")
        auth_overflow=page.evaluate("Array.from(document.querySelectorAll('.authority-enforcement-r85,.learning-authority-r85,.recall-authority-empty-r85')).some(el => el.scrollWidth > el.clientWidth + 1)")
        select_overflow=page.evaluate("Array.from(document.querySelectorAll('select,textarea')).some(el => el.getBoundingClientRect().right > document.documentElement.clientWidth + 1)")
        results.append((width,overflow,auth_overflow,select_overflow))
        if width in (1440,390):
            page.screenshot(path=str(OUT/f'ui_r85_rev1_authority_enforcement_{width}.png'),full_page=True)
    browser.close()
for item in results: print(item)
if any(any(item[1:]) for item in results): raise SystemExit('UI-R85 browser sweep failed')
print('UI-R85 REV1 browser sweep PASS')
