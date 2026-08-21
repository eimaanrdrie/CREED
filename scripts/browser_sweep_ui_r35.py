"""UI-R35 AI Runtime execution-proof overflow sweep using CREED's real CSS."""
from pathlib import Path
import json, re, shutil, sys
ROOT = Path(__file__).resolve().parents[1]
CSS = (ROOT / "frontend" / "app" / "globals.css").read_text(encoding="utf-8")
HARNESS = (ROOT / "scripts" / "fixtures" / "ui_r35_runtime_harness.html").read_text(encoding="utf-8")
WIDTHS = [320, 360, 390, 430, 620, 768, 860, 1024, 1180, 1280, 1366, 1440, 1600, 1920]
try:
    from playwright.sync_api import sync_playwright
except ImportError:
    print("SKIP: Python Playwright is not installed")
    sys.exit(2)
chromium = shutil.which("chromium") or shutil.which("chromium-browser") or shutil.which("google-chrome")
if not chromium:
    print("SKIP: Chromium executable not found")
    sys.exit(2)
css = re.sub(r'^@import\\s+"tailwindcss";\\s*', "", CSS)
html = re.sub(r'<link rel="stylesheet"[^>]*>', "<style>" + css + "</style>", HARNESS, count=1)
failed=[]
with sync_playwright() as p:
    browser=p.chromium.launch(executable_path=chromium,headless=True,args=["--no-sandbox","--disable-dev-shm-usage","--disable-gpu"])
    for width in WIDTHS:
        page=browser.new_page(viewport={"width":width,"height":900})
        page.set_content(html,wait_until="load",timeout=20_000)
        report=json.loads(page.locator("#overflow-report").inner_text())
        ok=not report["pageOverflow"] and not report["failures"]
        print(f"{width:4d}px: {'PASS' if ok else 'FAIL'}")
        if not ok: failed.append((width,report))
        page.close()
    browser.close()
if failed:
    print(json.dumps(failed,indent=2)); sys.exit(1)
print("UI-R35 runtime execution-proof browser sweep: PASS")
