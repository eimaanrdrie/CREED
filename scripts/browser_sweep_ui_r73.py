"""UI-R73 AI Runtime alignment + overflow sweep using actual CREED CSS."""
from pathlib import Path
import json, re, shutil, sys
ROOT = Path(__file__).resolve().parents[1]
CSS = (ROOT / "frontend/app/globals.css").read_text(encoding="utf-8")
HARNESS = (ROOT / "scripts/fixtures/ui_r73_runtime_alignment_harness.html").read_text(encoding="utf-8")
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
    page = browser.new_page(viewport={"width": 1500, "height": 5200})
    page.set_content(html, wait_until="load", timeout=20_000)
    page.wait_for_timeout(100)
    report = json.loads(page.locator("#report").inner_text())
    page.screenshot(path=str(ROOT / "scripts/fixtures/ui_r73_runtime_alignment_preview.png"), full_page=True)
    browser.close()
if report["pageOverflow"] or report["failures"]:
    print(json.dumps(report, indent=2))
    sys.exit(1)
print("UI-R73 AI Runtime alignment + overflow sweep: PASS")
for item in report["geometry"]:
    print(f"- {item['width']}px rail offsets: {item['offsets']}; metric widths: {[round(v, 1) for v in item['metrics']]}")
