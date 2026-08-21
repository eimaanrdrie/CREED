"""UI-R77 REV1 Evidence overflow + reading-width sweep using actual CREED CSS."""
from pathlib import Path
import json, re, shutil, sys
ROOT = Path(__file__).resolve().parents[1]
CSS = (ROOT / "frontend/app/globals.css").read_text(encoding="utf-8")
HARNESS = (ROOT / "scripts/fixtures/ui_r77_rev1_evidence_harness.html").read_text(encoding="utf-8")
try:
    from playwright.sync_api import sync_playwright
except ImportError:
    print("SKIP: Python Playwright is not installed")
    sys.exit(2)
chromium = shutil.which("chromium") or shutil.which("chromium-browser") or shutil.which("google-chrome")
if not chromium:
    print("SKIP: Chromium executable not found")
    sys.exit(2)
css = re.sub(r'^@import\s+"tailwindcss";\s*', "", CSS)
html = re.sub(r'<link rel="stylesheet"[^>]*>', "<style>" + css + "</style>", HARNESS, count=1)
with sync_playwright() as p:
    browser = p.chromium.launch(executable_path=chromium, headless=True, args=["--no-sandbox", "--disable-dev-shm-usage", "--disable-gpu"])
    page = browser.new_page(viewport={"width": 1500, "height": 1800})
    page.set_content(html, wait_until="load", timeout=20_000)
    page.wait_for_function("document.querySelector('#report').innerText.includes('results')", timeout=10_000)
    report = json.loads(page.locator("#report").inner_text())
    page.locator("#stage").evaluate("el => el.style.width='1180px'")
    page.wait_for_timeout(50)
    page.screenshot(path=str(ROOT / "scripts/fixtures/ui_r77_rev1_evidence_preview.png"), full_page=True)
    browser.close()
if report["pageOverflow"] or report["failures"]:
    print(json.dumps(report, indent=2))
    sys.exit(1)
# Reading measure must remain bounded on the two-pane desktop widths.
for item in report["results"]:
    if item["width"] >= 980 and item["excerptWidth"] > 700:
        print(json.dumps(report, indent=2))
        raise SystemExit(f"Excerpt too wide at {item['width']}px: {item['excerptWidth']}px")
print("UI-R77 REV1 Evidence overflow + reading-width sweep: PASS")
for item in report["results"]:
    print(f"- {item['width']}px layout={item['layout']} excerpt={item['excerptWidth']}px")
