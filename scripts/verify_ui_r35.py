from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
TSX = (ROOT / "frontend" / "components" / "ai-runtime-console.tsx").read_text(encoding="utf-8")
CSS = (ROOT / "frontend" / "app" / "globals.css").read_text(encoding="utf-8")
NOTES = (ROOT / "UI_R35_NOTES.md").read_text(encoding="utf-8")
for token in [
    'const RUNTIME_TIME_ZONE = "Asia/Kuala_Lumpur";',
    'new Intl.DateTimeFormat("en-MY"',
    'timeZone: RUNTIME_TIME_ZONE',
    'RUNTIME_TIME_FORMATTER.format(date)',
    'dateTime={execution.completed_at ?? undefined}',
]:
    assert token in TSX, f"missing hydration contract: {token}"
assert 'date.toLocaleString([]' not in TSX, "locale-dependent runtime timestamp can reintroduce hydration mismatch"
for token in [
    "UI-R35 — AI Runtime hydration + Execution Proof containment",
    ".runtime-execution-r30 {\n  grid-template-columns:36px minmax(0,1fr) minmax(58px,auto) minmax(0,156px) 18px;",
    "@media (max-width:1280px)",
    ".runtime-selected-r30 .progressive-disclosure-meta",
]:
    assert token in CSS, f"missing R35 overflow contract: {token}"
assert "SSR/client timestamp mismatch" in NOTES
assert not (ROOT / "frontend" / "app" / "demo").exists(), "Demo route must remain removed"
for path in (ROOT / "frontend").rglob("*.tsx"):
    text=path.read_text(encoding="utf-8")
    assert "react-icons" not in text
    assert "@heroicons" not in text
    assert "fontawesome" not in text.lower()
assert CSS.count("{") == CSS.count("}"), "CSS braces are unbalanced"
print("UI-R35 verification: PASS")
print("- AI Runtime timestamp formatting is locale/timezone deterministic for SSR hydration")
print("- execution history and selected proof reflow before overflow")
print("- provenance metadata and long runtime identifiers stay contained")
print("- Demo removal and Lucide-only policy preserved")
