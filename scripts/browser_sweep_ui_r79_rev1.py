from pathlib import Path
import json,re,shutil,sys
ROOT=Path(__file__).resolve().parents[1]
CSS=(ROOT/'frontend/app/globals.css').read_text(encoding='utf-8')
HARNESS=(ROOT/'scripts/fixtures/ui_r79_rev1_human_decision_harness.html').read_text(encoding='utf-8')
try:
    from playwright.sync_api import sync_playwright
except ImportError:
    print('SKIP: Python Playwright is not installed'); sys.exit(2)
chromium=shutil.which('chromium') or shutil.which('chromium-browser') or shutil.which('google-chrome')
if not chromium:
    print('SKIP: Chromium executable not found'); sys.exit(2)
css=re.sub(r'^@import\s+"tailwindcss";\s*','',CSS)
html=re.sub(r'<link rel="stylesheet"[^>]*>','<style>'+css+'</style>',HARNESS,count=1)
with sync_playwright() as p:
    browser=p.chromium.launch(executable_path=chromium,headless=True,args=['--no-sandbox','--disable-dev-shm-usage','--disable-gpu'])
    page=browser.new_page(viewport={'width':1500,'height':1000})
    page.set_content(html,wait_until='load',timeout=20000)
    report=json.loads(page.locator('#report').inner_text())
    page.screenshot(path=str(ROOT/'scripts/fixtures/ui_r79_rev1_human_decision_preview.png'),full_page=True)
    browser.close()
if report['pageOverflow'] or report['failures']:
    print(json.dumps(report,indent=2)); sys.exit(1)
if report['transitionProperty'] != 'transform':
    print(json.dumps(report,indent=2)); raise SystemExit('Progress still transitions a layout property')
# Full-width bar should match track width before scale transform.
try:
    bw=float(report['barWidth'].replace('px','')); tw=float(report['trackWidth'].replace('px',''))
except Exception:
    raise SystemExit('Could not parse progress geometry')
if abs(bw-tw)>1.5:
    print(json.dumps(report,indent=2)); raise SystemExit('Progress bar is not full track width before scale')
if report['affectedIcon'] == report['selectedIcon']:
    print(json.dumps(report,indent=2)); raise SystemExit('Selected human outcome did not gain semantic emphasis')
if report['aiAdvisory'] == report['action']:
    print(json.dumps(report,indent=2)); raise SystemExit('AI advisory competes with action-required signal')
print('UI-R79 REV1 Human Decision motion/authority sweep: PASS')
print(json.dumps(report,indent=2))
