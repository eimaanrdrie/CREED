from pathlib import Path
import os
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
HTML = (ROOT / "scripts/fixtures/ui_r90_rev1_modules_harness.html").resolve()
OUT = ROOT / "scripts/fixtures"
viewports = [(1440,900),(1100,800),(900,760),(760,844),(560,844),(390,844)]
results=[]
with sync_playwright() as p:
    exe=p.chromium.executable_path if os.path.exists(p.chromium.executable_path) else ("/usr/bin/chromium" if os.path.exists("/usr/bin/chromium") else None)
    kwargs={"headless":True,"args":["--no-sandbox"]}
    if exe: kwargs["executable_path"]=exe
    browser=p.chromium.launch(**kwargs)
    page=browser.new_page(viewport={"width":1440,"height":900})
    for width,height in viewports:
        page.set_viewport_size({"width":width,"height":height})
        page.set_content(HTML.read_text(encoding="utf-8"), wait_until="load")
        root_overflow=page.evaluate("document.documentElement.scrollWidth > document.documentElement.clientWidth + 1")
        page_overflow=page.locator(".module-registry-r90").evaluate("el => el.scrollWidth > el.clientWidth + 1")
        results.append((width,height,root_overflow,page_overflow))
        if width==1440:
            page.screenshot(path=str(OUT/"ui_r90_rev1_modules_1440.png"), full_page=False)
            page.locator(".preview-add-r90").click()
            page.screenshot(path=str(OUT/"ui_r90_rev1_modules_create_1440.png"), full_page=False)
        if width==390:
            page.screenshot(path=str(OUT/"ui_r90_rev1_modules_390.png"), full_page=True)
    # Explicit seven-item flyout check at short laptop height.
    page.set_viewport_size({"width":800,"height":650})
    page.set_content(HTML.read_text(encoding="utf-8"), wait_until="load")
    page.locator(".preview-registry-r90").click()
    flyout=page.locator(".preview-flyout-r90")
    box=flyout.bounding_box()
    flyout_inside=bool(box) and box["y"] >= 0 and box["y"] + box["height"] <= 650
    flyout_internal_scroll=flyout.evaluate("el => el.scrollHeight > el.clientHeight + 1")
    page.screenshot(path=str(OUT/"ui_r90_rev1_registry_flyout_800x650.png"), full_page=False)
    browser.close()

for item in results: print(item)
print("flyout_inside", flyout_inside, "flyout_internal_scroll", flyout_internal_scroll)
if any(item[2] or item[3] for item in results) or not flyout_inside or flyout_internal_scroll:
    raise SystemExit("UI-R90 REV1 browser sweep failed")
print("UI-R90 REV1 browser sweep PASS")
