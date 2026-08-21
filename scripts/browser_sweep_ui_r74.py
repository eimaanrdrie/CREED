"""UI-R74 computed palette + overflow sweep using actual CREED CSS."""
from pathlib import Path
import json, re, shutil, sys

ROOT = Path(__file__).resolve().parents[1]
CSS = (ROOT / "frontend/app/globals.css").read_text(encoding="utf-8")
HARNESS = (ROOT / "scripts/fixtures/ui_r74_palette_harness.html").read_text(encoding="utf-8")
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
expected = {
  "--creed-background": "#071019",
  "--creed-surface": "#0B1724",
  "--creed-raised": "#102033",
  "--creed-off-white": "#F3EDE3",
  "--creed-secondary": "#A8B5C3",
  "--creed-muted": "#7D8A98",
  "--creed-hairline": "#1B2A3A",
  "--creed-action": "#7CC7D9",
  "--creed-success": "#6FBF9E",
  "--creed-warning": "#D6A86B",
  "--creed-danger": "#C96B6B",
}

with sync_playwright() as p:
    browser = p.chromium.launch(executable_path=chromium, headless=True, args=["--no-sandbox", "--disable-dev-shm-usage", "--disable-gpu"])
    page = browser.new_page(viewport={"width": 1440, "height": 1200})
    page.set_content(html, wait_until="load", timeout=20_000)
    page.wait_for_timeout(100)
    report = json.loads(page.locator("#report").inner_text())
    page.screenshot(path=str(ROOT / "scripts/fixtures/ui_r74_palette_preview.png"), full_page=True)
    browser.close()

failures = []
for key, value in expected.items():
    if report["tokens"].get(key).upper() != value.upper():
        failures.append(f"{key}: expected {value}, got {report['tokens'].get(key)}")
expected_computed = {
    "bodyBg": "rgb(7, 16, 25)",
    "surfaceBg": "rgb(11, 23, 36)",
    "raisedBg": "rgb(16, 32, 51)",
    "heading": "rgb(243, 237, 227)",
    "subtitle": "rgb(168, 181, 195)",
    "primaryBg": "rgb(124, 199, 217)",
    "primaryColor": "rgb(7, 16, 25)",
    "activeBg": "rgb(16, 32, 51)",
    "activeColor": "rgb(243, 237, 227)",
}
for key, value in expected_computed.items():
    if report.get(key) != value:
        failures.append(f"{key}: expected {value}, got {report.get(key)}")
if report["pageOverflow"]:
    failures.append("page overflow detected")
if failures:
    print(json.dumps({"failures": failures, "report": report}, indent=2))
    sys.exit(1)
print("UI-R74 computed palette + overflow sweep: PASS")
for key in ["bodyBg","surfaceBg","raisedBg","heading","subtitle","primaryBg","activeBg","selectedRuntimeBg"]:
    print(f"- {key}: {report[key]}")
