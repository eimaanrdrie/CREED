from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CSS = (ROOT / "frontend" / "app" / "globals.css").read_text(encoding="utf-8")
DASH = (ROOT / "frontend" / "components" / "final-dashboard.tsx").read_text(encoding="utf-8")

required_css = [
    "UI-R13 — Overview command-center recomposition",
    "max-width: 1320px",
    "grid-template-columns: repeat(3, minmax(0, 1fr))",
    "@media (max-width: 1180px)",
    "@media (max-width: 820px)",
    "@media (max-width: 560px)",
    ".assurance-loop-track",
]
for token in required_css:
    assert token in CSS, f"missing UI-R13 CSS contract: {token}"

assert "overview-r02" in DASH
assert "attention-grid" in DASH
assert "overview-two-column" in DASH
assert "assurance-loop-track" in DASH

# Approved policy regression checks.
assert not (ROOT / "frontend" / "app" / "demo").exists(), "Demo route must remain removed"
for path in (ROOT / "frontend").rglob("*.tsx"):
    text = path.read_text(encoding="utf-8")
    assert "react-icons" not in text
    assert "@heroicons" not in text
    assert "fontawesome" not in text.lower()

print("UI-R13 verification: PASS")
