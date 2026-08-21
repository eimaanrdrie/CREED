from pathlib import Path
import os
from playwright.sync_api import sync_playwright

ROOT=Path(__file__).resolve().parents[1]
HTML=(ROOT/'scripts/fixtures/ui_r83_rev1_dependency_registry_harness.html').resolve()
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
        height=1100 if width>760 else 1100
        page.set_viewport_size({"width":width,"height":height})
        page.set_content(HTML.read_text(encoding="utf-8"),wait_until="load")
        overflow=page.evaluate("document.documentElement.scrollWidth > document.documentElement.clientWidth")
        row_overflow=page.evaluate("Array.from(document.querySelectorAll('.dependency-row-r83')).some(el => el.scrollWidth > el.clientWidth + 1)")
        create_overflow=page.evaluate("document.querySelector('.dependency-create-r83').scrollWidth > document.querySelector('.dependency-create-r83').clientWidth + 1")
        remove_overflow=page.evaluate("document.querySelector('.dependency-remove-r83').scrollWidth > document.querySelector('.dependency-remove-r83').clientWidth + 1")
        results.append((width,overflow,row_overflow,create_overflow,remove_overflow))
        if width in (1440,390):
            page.screenshot(path=str(OUT/f'ui_r83_rev1_dependencies_{width}.png'),full_page=True)
    browser.close()
for item in results: print(item)
if any(any(item[1:]) for item in results): raise SystemExit('UI-R83 browser sweep failed')
print('UI-R83 REV1 browser sweep PASS')
