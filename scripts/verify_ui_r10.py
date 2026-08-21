from __future__ import annotations

from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
FRONTEND = ROOT / "frontend"
issues: list[str] = []

for path in FRONTEND.rglob("*"):
    if not path.is_file() or path.suffix not in {".ts", ".tsx", ".css", ".md"}:
        continue
    text = path.read_text(encoding="utf-8", errors="ignore")
    if "/demo" in text or "DemoWorkspace" in text or "PlayCircle" in text:
        issues.append(f"Demo UI reference remains: {path.relative_to(ROOT)}")

for path in FRONTEND.rglob("*.tsx"):
    text = path.read_text(encoding="utf-8")
    if re.search(r"<svg\b", text, re.IGNORECASE):
        issues.append(f"Raw SVG found: {path.relative_to(ROOT)}")
    for match in re.finditer(r"from\s+[\"']([^\"']+)[\"']", text):
        module = match.group(1).lower()
        if any(name in module for name in ("heroicons", "react-icons", "phosphor", "fontawesome", "iconsax")):
            issues.append(f"Secondary icon library {module}: {path.relative_to(ROOT)}")
    if re.search(r"<button(?![^>]*\btype=)[^>]*>", text, re.DOTALL):
        issues.append(f"Button without explicit type: {path.relative_to(ROOT)}")

shell = (FRONTEND / "components" / "app-shell.tsx").read_text(encoding="utf-8")
sidebar = (FRONTEND / "components" / "sidebar.tsx").read_text(encoding="utf-8")
css = (FRONTEND / "app" / "globals.css").read_text(encoding="utf-8")

requirements = {
    "skip-to-main": 'className="skip-link"',
    "main focus target": 'id="main-content"',
    "menu expanded state": "aria-expanded={navOpen}",
    "Escape closes mobile navigation": 'event.key === "Escape"',
    "focus restored to menu trigger": "menuButtonRef.current?.focus()",
}
for label, token in requirements.items():
    if token not in shell:
        issues.append(f"Missing shell accessibility behavior: {label}")

if 'aria-current={active === label ? "page" : undefined}' not in sidebar:
    issues.append("Primary navigation does not expose aria-current=page")

for label, token in {
    "coarse-pointer touch target": "min-height:44px",
    "mobile form text floor": "font-size:16px!important",
    "reduced motion": "@media (prefers-reduced-motion: reduce)",
    "increased contrast": "@media (prefers-contrast: more)",
    "safe-area support": "env(safe-area-inset-left)",
}.items():
    if token not in css:
        issues.append(f"Missing final CSS behavior: {label}")

if css.count("{") != css.count("}"):
    issues.append("CSS brace count is unbalanced")

if issues:
    print("FAIL: UI-R10 final policy verification")
    for issue in issues:
        print(f"- {issue}")
    sys.exit(1)

print("PASS: UI-R10 final policy verification")
print("- Demo UI removed")
print("- Lucide-only icon policy enforced")
print("- explicit button types enforced")
print("- skip navigation + keyboard mobile navigation present")
print("- touch/form/overflow hardening present")
print("- reduced-motion + increased-contrast support present")
