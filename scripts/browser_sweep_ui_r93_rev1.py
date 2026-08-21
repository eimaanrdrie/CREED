from pathlib import Path
import os
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
HTML = (ROOT / 'scripts/fixtures/ui_r93_rev1_system_health_harness.html').resolve()
OUT = ROOT / 'scripts/fixtures'
viewports = [(1440, 900), (1100, 700), (800, 650)]
results = []

with sync_playwright() as p:
    default = p.chromium.executable_path
    executable = default if os.path.exists(default) else ('/usr/bin/chromium' if os.path.exists('/usr/bin/chromium') else None)
    kwargs = {'headless': True, 'args': ['--no-sandbox']}
    if executable:
        kwargs['executable_path'] = executable
    browser = p.chromium.launch(**kwargs)
    page = browser.new_page(viewport={'width': 1440, 'height': 900})
    html = HTML.read_text(encoding='utf-8')

    for width, height in viewports:
        page.set_viewport_size({'width': width, 'height': height})
        page.set_content(html, wait_until='load')
        overflow = page.evaluate('document.documentElement.scrollWidth > document.documentElement.clientWidth')
        rows = page.locator('#system-health .system-health-row').count()
        runtime_links_total = page.locator('a[href="/ai-runtime"]').count()
        runtime_links_health = page.locator('#system-health a[href="/ai-runtime"]').count()
        health = page.locator('#system-health').bounding_box()
        if not health:
            raise SystemExit('UI-R93 system health geometry unavailable')
        bounded = health['y'] >= -0.5 and health['y'] + health['height'] <= height + 0.5
        labels = page.locator('#system-health .system-health-row > span:nth-child(2)').all_text_contents()
        results.append((width, height, overflow, rows, runtime_links_total, runtime_links_health, bounded, labels))
        if (width, height) in ((1440, 900), (800, 650)):
            page.screenshot(path=str(OUT / f'ui_r93_rev1_system_health_{width}x{height}.png'), full_page=True)

    # Mobile overlay remains bounded and still contains health only.
    page.set_viewport_size({'width': 760, 'height': 844})
    page.set_content(html, wait_until='load')
    page.evaluate("document.querySelector('.sidebar').classList.add('sidebar-mobile')")
    mobile_health = page.locator('#system-health').bounding_box()
    mobile_runtime_links_health = page.locator('#system-health a[href="/ai-runtime"]').count()
    mobile_rows = page.locator('#system-health .system-health-row').count()
    if not mobile_health:
        raise SystemExit('UI-R93 mobile health geometry unavailable')
    results.append(('mobile', 760, 844, mobile_rows, mobile_runtime_links_health))
    browser.close()

for item in results:
    print(item)

expected_labels = ['API', 'Database', 'Qwen', 'Knowledge Source']
for item in results:
    if item[0] == 'mobile':
        if item[3] != 4 or item[4] != 0:
            raise SystemExit('UI-R93 mobile System Health content regression')
    else:
        _, _, overflow, rows, runtime_total, runtime_health, bounded, labels = item
        if overflow or rows != 4 or runtime_total != 1 or runtime_health != 0 or not bounded or labels != expected_labels:
            raise SystemExit('UI-R93 desktop System Health regression')
print('UI-R93 REV1 browser sweep PASS')
