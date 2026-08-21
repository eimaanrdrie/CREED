from pathlib import Path
import os
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
HTML = (ROOT / "scripts/fixtures/ui_r87_rev1_ownership_harness.html").resolve()
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
    page = browser.new_page(viewport={"width": 1440, "height": 1200})
    for width in widths:
        page.set_viewport_size({"width": width, "height": 1200})
        page.set_content(HTML.read_text(encoding="utf-8"), wait_until="load")
        root_overflow = page.evaluate("document.documentElement.scrollWidth > document.documentElement.clientWidth")
        local_overflow = page.evaluate("Array.from(document.querySelectorAll('.ownership-registry-r87,.ownership-create-r87,.ownership-ledger-r87,.ownership-row-r87')).some(el => el.scrollWidth > el.clientWidth + 1)")
        controls_overflow = page.evaluate("Array.from(document.querySelectorAll('input,select,textarea,button')).some(el => el.getBoundingClientRect().right > document.documentElement.clientWidth + 1)")
        results.append((width, root_overflow, local_overflow, controls_overflow))
        if width in (1440, 390):
            page.screenshot(path=str(OUT / f"ui_r87_rev1_ownership_{width}.png"), full_page=True)
    browser.close()
for item in results:
    print(item)
if any(any(item[1:]) for item in results):
    raise SystemExit("UI-R87 browser sweep failed")
print("UI-R87 REV1 browser sweep PASS")
