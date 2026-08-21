from pathlib import Path
import os
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
HTML = (ROOT / "scripts/fixtures/ui_r89_rev1_products_harness.html").resolve()
OUT = ROOT / "scripts/fixtures"
viewports = [(1440,900),(1100,800),(900,760),(760,844),(560,844),(390,844)]
results = []

with sync_playwright() as p:
    default_exe = p.chromium.executable_path
    executable = default_exe if os.path.exists(default_exe) else ("/usr/bin/chromium" if os.path.exists("/usr/bin/chromium") else None)
    kwargs = {"headless": True, "args": ["--no-sandbox"]}
    if executable:
        kwargs["executable_path"] = executable
    browser = p.chromium.launch(**kwargs)
    page = browser.new_page(viewport={"width":1440,"height":900})
    for width,height in viewports:
        page.set_viewport_size({"width":width,"height":height})
        page.set_content(HTML.read_text(encoding="utf-8"), wait_until="load")
        root_overflow = page.evaluate("document.documentElement.scrollWidth > document.documentElement.clientWidth + 1")
        page_overflow = page.locator(".product-registry-r89").evaluate("el => el.scrollWidth > el.clientWidth + 1")
        results.append((width,height,root_overflow,page_overflow))

        if width == 1440:
            page.screenshot(path=str(OUT/"ui_r89_rev1_products_1440.png"), full_page=False)
            page.locator(".preview-add-r89").click()
            page.screenshot(path=str(OUT/"ui_r89_rev1_products_create_1440.png"), full_page=False)
        if width == 390:
            page.screenshot(path=str(OUT/"ui_r89_rev1_products_390.png"), full_page=True)
    browser.close()

for item in results:
    print(item)
if any(item[2] or item[3] for item in results):
    raise SystemExit("UI-R89 REV1 browser sweep failed")
print("UI-R89 REV1 browser sweep PASS")
