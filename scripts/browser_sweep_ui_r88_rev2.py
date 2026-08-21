from pathlib import Path
import os
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
HTML = (ROOT / "scripts/fixtures/ui_r88_rev2_sidebar_harness.html").resolve()
OUT = ROOT / "scripts/fixtures"
# Desktop includes short laptop heights to verify that the rail itself does not scroll.
viewports = [
    (1440, 900),
    (1100, 768),
    (900, 700),
    (800, 650),
    (760, 844),
    (560, 844),
    (390, 844),
]
results = []
with sync_playwright() as p:
    default_exe = p.chromium.executable_path
    executable = default_exe if os.path.exists(default_exe) else ("/usr/bin/chromium" if os.path.exists("/usr/bin/chromium") else None)
    launch_kwargs = {"headless": True, "args": ["--no-sandbox"]}
    if executable:
        launch_kwargs["executable_path"] = executable
    browser = p.chromium.launch(**launch_kwargs)
    page = browser.new_page(viewport={"width": 1440, "height": 900})
    for width, height in viewports:
        page.set_viewport_size({"width": width, "height": height})
        page.set_content(HTML.read_text(encoding="utf-8"), wait_until="load")
        root_overflow = page.evaluate("document.documentElement.scrollWidth > document.documentElement.clientWidth")
        visible_sidebars = page.locator('.sidebar:visible')
        sidebar_count = visible_sidebars.count()
        sidebar_horizontal = False
        sidebar_vertical = False
        nav_scroll_mode = []
        for i in range(sidebar_count):
            el = visible_sidebars.nth(i)
            sidebar_horizontal = sidebar_horizontal or el.evaluate("el => el.scrollWidth > el.clientWidth + 1")
            if width > 760:
                sidebar_vertical = sidebar_vertical or el.evaluate("el => el.scrollHeight > el.clientHeight + 1")
            nav_scroll_mode.append(el.locator('.nav-primary').evaluate("el => getComputedStyle(el).overflowY"))
        results.append((width, height, root_overflow, sidebar_horizontal, sidebar_vertical, nav_scroll_mode))

        if width == 1440:
            page.screenshot(path=str(OUT / "ui_r88_rev2_sidebar_collapsed_1440.png"), full_page=False)
            registry = page.locator('.preview-shell-r88 .nav-group-toggle', has_text='Registry')
            registry.click()
            if registry.get_attribute('aria-expanded') != 'true':
                raise SystemExit('Registry flyout did not open in desktop harness')
            flyout = page.locator('.preview-shell-r88 #registry-panel')
            if not flyout.is_visible():
                raise SystemExit('Registry flyout not visible after activation')
            page.screenshot(path=str(OUT / "ui_r88_rev2_sidebar_registry_flyout_1440.png"), full_page=False)
            system = page.locator('.preview-shell-r88 .system-summary-btn')
            system.click()
            if system.get_attribute('aria-expanded') != 'true':
                raise SystemExit('System health popover did not open')
            page.screenshot(path=str(OUT / "ui_r88_rev2_sidebar_system_1440.png"), full_page=False)
        if width == 390:
            registry = page.locator('.preview-mobile-layer-r88 .nav-group-toggle', has_text='Registry')
            registry.click()
            panel = page.locator('.preview-mobile-layer-r88 #registry-panel')
            if not panel.is_visible():
                raise SystemExit('Mobile registry overlay did not open')
            panel_box = panel.bounding_box()
            if not panel_box or panel_box['x'] < 0 or panel_box['x'] + panel_box['width'] > width + 1:
                raise SystemExit('Mobile registry overlay escaped viewport')
            page.screenshot(path=str(OUT / "ui_r88_rev2_sidebar_mobile_390.png"), full_page=False)
    browser.close()

for item in results:
    print(item)
if any(item[2] or item[3] or item[4] for item in results):
    raise SystemExit("UI-R88 REV2 browser sweep failed")
# Desktop nav must not be an internal scroll region; mobile overlays may scroll internally.
for width, _, _, _, _, modes in results:
    if width > 760 and any(mode in {"auto", "scroll"} for mode in modes):
        raise SystemExit(f"Desktop nav has scroll overflow at {width}px: {modes}")
print("UI-R88 REV2 browser sweep PASS")
