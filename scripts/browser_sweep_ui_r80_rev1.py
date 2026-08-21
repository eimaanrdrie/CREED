from pathlib import Path
import os
from playwright.sync_api import sync_playwright

ROOT=Path(__file__).resolve().parents[1]
HTML=(ROOT/'scripts/fixtures/ui_r80_rev1_client_registry_harness.html').resolve()
OUT=ROOT/'scripts/fixtures'
widths=[1440,1000,760,390]
results=[]
with sync_playwright() as p:
    default_exe = p.chromium.executable_path
    executable = default_exe if os.path.exists(default_exe) else ("/usr/bin/chromium" if os.path.exists("/usr/bin/chromium") else None)
    launch_kwargs = {"headless": True, "args": ["--no-sandbox"]}
    if executable:
        launch_kwargs["executable_path"] = executable
    browser=p.chromium.launch(**launch_kwargs)
    page=browser.new_page(viewport={"width":1440,"height":900})
    for width in widths:
        height=900 if width>760 else 844
        page.set_viewport_size({"width":width,"height":height})
        page.set_content(HTML.read_text(encoding="utf-8"), wait_until="load")
        overflow=page.evaluate("document.documentElement.scrollWidth > document.documentElement.clientWidth")
        row_overflow=page.evaluate("Array.from(document.querySelectorAll('.client-row-r80')).some(el => el.scrollWidth > el.clientWidth + 1)")
        create_overflow=page.evaluate("document.querySelector('.client-create-r80').scrollWidth > document.querySelector('.client-create-r80').clientWidth + 1")
        results.append((width,overflow,row_overflow,create_overflow))
        if width in (1440,390):
            page.screenshot(path=str(OUT/f'ui_r80_rev1_clients_{width}.png'), full_page=True)
    browser.close()
for item in results: print(item)
if any(any(item[1:]) for item in results): raise SystemExit('UI-R80 browser sweep failed')
print('UI-R80 REV1 browser sweep PASS')
