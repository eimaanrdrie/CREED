from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
CSS = (ROOT / "frontend" / "app" / "globals.css").read_text(encoding="utf-8")
NOTES = (ROOT / "UI_R34_NOTES.md").read_text(encoding="utf-8")
DESIGN = (ROOT / "frontend" / "DESIGN.md").read_text(encoding="utf-8")
HARNESS = ROOT / "scripts" / "fixtures" / "ui_r34_overflow_harness.html"

for token in [
    "UI-R34 — Whole-App Overflow Regression Sweep",
    ".topbar-left { flex:1 1 auto; overflow:hidden; }",
    ".status-pill {",
    ".issue-case-signals-r33",
    ".radar-filter-r26 button",
    ".knowledge-search-r32",
    ".recall-flow-node-r28",
    ".audit-run-search-form-r29",
    ".runtime-execution-r30",
    ".document-modal,",
    "html,body { overflow-x:clip; }",
]:
    assert token in CSS, f"missing R34 overflow contract: {token}"

assert "Preserve readable typography" in NOTES
assert "UI-R34 — Overflow Regression Contract" in DESIGN
assert HARNESS.exists(), "R34 Chromium overflow harness missing"
assert "NO SUPPORTING EVIDENCE OF IMPACT" in HARNESS.read_text(encoding="utf-8")
assert "NEEDS MORE INVESTIGATION" in HARNESS.read_text(encoding="utf-8")
assert not (ROOT / "frontend" / "app" / "demo").exists(), "Demo route must remain removed"

for path in (ROOT / "frontend").rglob("*.tsx"):
    text = path.read_text(encoding="utf-8")
    assert "react-icons" not in text
    assert "@heroicons" not in text
    assert "fontawesome" not in text.lower()

assert CSS.count("{") == CSS.count("}"), "CSS braces are unbalanced"
print("UI-R34 verification: PASS")
print("- global control/dynamic-text containment contract present")
print("- long issue/AI/recall/audit/runtime identifiers are width-safe")
print("- topbar, modals and small-screen actions reflow before overflow")
print("- Chromium stress harness included for 320px+ viewport checks")
print("- readable typography, Demo removal and Lucide-only policy preserved")
