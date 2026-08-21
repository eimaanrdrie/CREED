from pathlib import Path
import os
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[1]
HTML=(ROOT/'scripts/fixtures/ui_r92_rev1_flyout_harness.html').resolve()
OUT=ROOT/'scripts/fixtures'
widths=[1440,1100,900,800]
heights=[900,768,700,650]
results=[]
with sync_playwright() as p:
    default=p.chromium.executable_path
    executable=default if os.path.exists(default) else ('/usr/bin/chromium' if os.path.exists('/usr/bin/chromium') else None)
    kwargs={'headless':True,'args':['--no-sandbox']}
    if executable: kwargs['executable_path']=executable
    browser=p.chromium.launch(**kwargs)
    page=browser.new_page(viewport={'width':1440,'height':900})
    html=HTML.read_text(encoding='utf-8')
    for width in widths:
        for height in heights:
            page.set_viewport_size({'width':width,'height':height})
            page.set_content(html,wait_until='load')
            page_overflow=page.evaluate('document.documentElement.scrollWidth > document.documentElement.clientWidth')
            flyout=page.locator('#registry-flyout').bounding_box()
            bridge=page.locator('.nav-flyout-bridge-r92').bounding_box()
            group=page.locator('#registry-group').bounding_box()
            if not flyout or not bridge or not group:
                raise SystemExit('R92 harness geometry unavailable')
            gap=flyout['x']-(group['x']+group['width'])
            bridge_right=bridge['x']+bridge['width']
            bridged=bridge['x'] <= group['x']+group['width']+0.5 and bridge_right >= flyout['x']-0.5
            bounded=flyout['y'] >= -0.5 and flyout['y']+flyout['height'] <= height+0.5
            results.append((width,height,page_overflow,round(gap,2),bridged,bounded))
            if (width,height) in ((1440,900),(800,650)):
                page.screenshot(path=str(OUT/f'ui_r92_rev1_flyout_{width}x{height}.png'),full_page=True)
    # Mobile boundary keeps the existing tap/overlay model and must not expose
    # the desktop pointer bridge.
    page.set_viewport_size({'width':760,'height':844})
    page.set_content(html,wait_until='load')
    page.evaluate("document.querySelector('.sidebar').classList.add('sidebar-mobile')")
    mobile_bridge_display=page.evaluate("getComputedStyle(document.querySelector('.nav-flyout-bridge-r92')).display")
    mobile_flyout=page.locator('#registry-flyout').bounding_box()
    if mobile_bridge_display != 'none' or not mobile_flyout:
        raise SystemExit('UI-R92 mobile overlay boundary failed')
    results.append(('mobile',760,844,mobile_bridge_display,round(mobile_flyout['width'],2)))
    browser.close()
for item in results: print(item)
if any(isinstance(item[0], int) and (item[2] or not item[4] or not item[5]) for item in results):
    raise SystemExit('UI-R92 browser sweep failed')
print('UI-R92 REV1 browser sweep PASS')
