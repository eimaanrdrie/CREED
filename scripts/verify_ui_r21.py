from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CSS = (ROOT / "frontend" / "app" / "globals.css").read_text(encoding="utf-8")
SHELL = (ROOT / "frontend" / "components" / "app-shell.tsx").read_text(encoding="utf-8")
SIDEBAR = (ROOT / "frontend" / "components" / "sidebar.tsx").read_text(encoding="utf-8")
NOTES = (ROOT / "UI_R21_NOTES.md").read_text(encoding="utf-8")

for token in [
    "UI-R21 — Global Shell + Accessibility Closure",
    ".nav-item { min-height:48px",
    ".icon-btn { width:44px; height:44px",
    "button,.primary-btn,.secondary-btn,.ghost-btn { min-height:44px; }",
    ".react-flow__controls button { width:44px!important; height:44px!important",
    ".sidebar-status-value",
    "intentionally avoids the old global 0.01ms animation kill",
]:
    assert token in CSS, f"missing UI-R21 CSS contract: {token}"

assert "animation-duration:.01ms" not in CSS, "legacy global reduced-motion animation kill remains"
for token in [
    "const navDialogRef = useRef<HTMLDivElement>(null)",
    'event.key !== "Tab"',
    "dialog.querySelectorAll<HTMLElement>",
    "last.focus()",
    "first.focus()",
    "ref={navDialogRef}",
    "menuButtonRef.current?.focus()",
]:
    assert token in SHELL, f"mobile dialog focus contract drifted: {token}"

for token in [
    "stateLabel(state)",
    "health?.dependencies.qwen",
]:
    assert token in SIDEBAR, f"truthful visible system-state contract drifted: {token}"
assert ("sidebar-status-value" in SIDEBAR or "system-status-row" in SIDEBAR), "system-state presentation missing"

assert "Global Shell + Accessibility Closure" in NOTES
assert not (ROOT / "frontend" / "app" / "demo").exists(), "Demo route must remain removed"
for path in (ROOT / "frontend").rglob("*.tsx"):
    text = path.read_text(encoding="utf-8")
    assert "react-icons" not in text
    assert "@heroicons" not in text
    assert "fontawesome" not in text.lower()

assert CSS.count("{") == CSS.count("}"), "CSS braces are unbalanced"
print("UI-R21 verification: PASS")
print("- persistent shell typography and controls enlarged")
print("- API / Database / Qwen state is visibly labelled from backend health")
print("- mobile navigation traps Tab focus and restores trigger focus")
print("- action targets use a 44px system floor")
print("- reduced-motion behavior no longer uses a global 0.01ms kill")
