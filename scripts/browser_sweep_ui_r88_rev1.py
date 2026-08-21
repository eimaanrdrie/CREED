from pathlib import Path
import os
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
HTML = (ROOT / "scripts/fixtures/ui_r88_rev1_sidebar_harness.html").resolve()
OUT = ROOT / "scripts/fixtures"
widths = [1440, 1100, 900, 760, 560, 390]
results = []
with sync_playwright() as p:
    default_exe = p.chromium.executable_path
    executable = default_exe if os.path.exists(default_exe) else ("/usr/bin/chromium" if os.path.exists("/usr/bin/chromium") else None)
    launch_kwargs = {"headless": True, "args": ["--no-sandbox"]}
    if executable:
        launch_kwargs["executable_path"] = executable
    browser = p.chromium.launch(**launch_kwargs)
    page = browser.new_page(viewport={"width": 1440, "height": 900})
    for width in widths:
        height = 900 if width > 760 else 844
        page.set_viewport_size({"width": width, "height": height})
        page.set_content(HTML.read_text(encoding="utf-8"), wait_until="load")
        root_overflow = page.evaluate("document.documentElement.scrollWidth > document.documentElement.clientWidth")
        visible_sidebar_overflow = page.evaluate("Array.from(document.querySelectorAll('.sidebar')).filter(el => getComputedStyle(el).display !== 'none').some(el => el.scrollWidth > el.clientWidth + 1)")
        collapsed_default = page.evaluate("Array.from(document.querySelectorAll('.nav-group-toggle')).filter(el => el.offsetParent !== null).every(el => el.getAttribute('aria-expanded') === 'false')")
        visible_registry = page.locator('.nav-group-toggle', has_text='Registry').filter(visible=True) if False else None
        results.append((width, root_overflow, visible_sidebar_overflow, collapsed_default))
        if width == 1440:
            page.screenshot(path=str(OUT / "ui_r88_rev1_sidebar_collapsed_1440.png"), full_page=False)
            page.locator('.preview-shell-r88 .nav-group-toggle', has_text='Registry').click()
            expanded = page.locator('.preview-shell-r88 .nav-group-toggle', has_text='Registry').get_attribute('aria-expanded') == 'true'
            if not expanded:
                raise SystemExit('Registry group did not expand in desktop harness')
            page.screenshot(path=str(OUT / "ui_r88_rev1_sidebar_registry_open_1440.png"), full_page=False)
        if width == 390:
            page.locator('.preview-mobile-layer-r88 .nav-group-toggle', has_text='Registry').click()
            page.screenshot(path=str(OUT / "ui_r88_rev1_sidebar_mobile_390.png"), full_page=False)
    browser.close()
for item in results:
    print(item)
if any(item[1] or item[2] or not item[3] for item in results):
    raise SystemExit("UI-R88 browser sweep failed")
print("UI-R88 REV1 browser sweep PASS")
