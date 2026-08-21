"""UI-R75 theme consistency + responsive overflow sweep using actual CREED CSS."""
from pathlib import Path
import json, re, shutil, sys

ROOT = Path(__file__).resolve().parents[1]
CSS = (ROOT / "frontend/app/globals.css").read_text(encoding="utf-8")
HARNESS = (ROOT / "scripts/fixtures/ui_r75_theme_consistency_harness.html").read_text(encoding="utf-8")
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
reports = []
with sync_playwright() as p:
    browser = p.chromium.launch(executable_path=chromium, headless=True, args=["--no-sandbox", "--disable-dev-shm-usage", "--disable-gpu"])
    for width in (1440, 900, 390):
        page = browser.new_page(viewport={"width": width, "height": 1600})
        page.set_content(html, wait_until="load", timeout=20_000)
        page.wait_for_timeout(80)
        base = page.evaluate("window.snapshot()")
        page.locator("#issueHover").hover()
        page.wait_for_timeout(180)
        hover = page.locator("#issueHover").evaluate("el => getComputedStyle(el).backgroundColor")
        base["issueHoverBg"] = hover
        base["width"] = width
        reports.append(base)
        if width == 1440:
            page.screenshot(path=str(ROOT / "scripts/fixtures/ui_r75_theme_consistency_preview.png"), full_page=True)
        page.close()
    browser.close()

failures = []
for r in reports:
    if r["panelBg"] != "rgb(11, 23, 36)": failures.append(f"{r['width']}: panel surface drift {r['panelBg']}")
    if r["panelBorder"] != "rgb(27, 42, 58)": failures.append(f"{r['width']}: panel border drift {r['panelBorder']}")
    if r["title"] != "rgb(243, 237, 227)": failures.append(f"{r['width']}: title color drift {r['title']}")
    if r["subtitle"] != "rgb(168, 181, 195)": failures.append(f"{r['width']}: subtitle color drift {r['subtitle']}")
    if r["okColor"] != "rgb(111, 191, 158)": failures.append(f"{r['width']}: success color drift {r['okColor']}")
    if r["warnColor"] != "rgb(214, 168, 107)": failures.append(f"{r['width']}: warning color drift {r['warnColor']}")
    if r["badColor"] != "rgb(201, 107, 107)": failures.append(f"{r['width']}: danger color drift {r['badColor']}")
    if r["infoColor"] != "rgb(124, 199, 217)": failures.append(f"{r['width']}: info color drift {r['infoColor']}")
    if r["okRadius"] != "5px" or r["infoRadius"] != "5px": failures.append(f"{r['width']}: semantic badge radius drift {r['okRadius']}/{r['infoRadius']}")
    if r["pageActiveBg"] != "rgb(16, 32, 51)": failures.append(f"{r['width']}: pagination active is not raised surface {r['pageActiveBg']}")
    if r["pageActiveColor"] != "rgb(243, 237, 227)": failures.append(f"{r['width']}: pagination active text drift {r['pageActiveColor']}")
    if r["pageActiveRadius"] != "5px": failures.append(f"{r['width']}: pagination radius drift {r['pageActiveRadius']}")
    if not (r["radarActiveBg"] == r["knowledgeActiveBg"] == r["auditActiveBg"] == r["runtimeSelectedBg"] == r["radarSelectedBg"]):
        failures.append(f"{r['width']}: selected-state backgrounds are inconsistent")
    if r["disclosureColor"] != "rgb(243, 237, 227)": failures.append(f"{r['width']}: open disclosure color drift {r['disclosureColor']}")
    if r["disclosureBorder"] != "rgb(27, 42, 58)": failures.append(f"{r['width']}: disclosure border drift {r['disclosureBorder']}")
    if r["issueHoverBg"] in ("rgba(0, 0, 0, 0)", "transparent"):
        failures.append(f"{r['width']}: hover feedback missing")
    if r["pageOverflow"]: failures.append(f"{r['width']}: page overflow detected")

if failures:
    print(json.dumps({"failures": failures, "reports": reports}, indent=2))
    sys.exit(1)
print("UI-R75 theme consistency + responsive overflow sweep: PASS")
for r in reports:
    print(f"- {r['width']}px: badges={r['okRadius']}, active-page={r['pageActiveBg']}, selected={r['runtimeSelectedBg']}, overflow={r['pageOverflow']}")
