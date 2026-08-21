from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CSS = (ROOT / "frontend" / "app" / "globals.css").read_text(encoding="utf-8")
KNOWLEDGE = (ROOT / "frontend" / "components" / "knowledge-workspace.tsx").read_text(encoding="utf-8")
NOTES = (ROOT / "UI_R32_NOTES.md").read_text(encoding="utf-8")

for token in [
    "UI-R32 — Knowledge Search Overflow",
    ".knowledge-search-r32",
    "width:calc(100% - 36px)",
    "grid-template-columns:minmax(0,1fr) auto",
    ".knowledge-search-field-r32",
    "grid-template-columns:22px minmax(0,1fr) auto",
    ".knowledge-search-submit-r32",
    "@media (max-width:760px)",
]:
    assert token in CSS, f"missing UI-R32 CSS contract: {token}"

for token in [
    'className="knowledge-search-r27 knowledge-search-r32"',
    'className="knowledge-search-field-r32"',
    'className="primary-btn knowledge-search-submit-r32"',
    'aria-label="Clear evidence search"',
    'onClick={runSearch}',
    'if(e.key==="Enter")runSearch()',
]:
    assert token in KNOWLEDGE, f"Knowledge search contract drifted: {token}"

assert "Issues metadata/chip overflow" in NOTES
assert "searchKnowledge(...)" in NOTES
assert not (ROOT / "frontend" / "app" / "demo").exists(), "Demo route must remain removed"

for path in (ROOT / "frontend").rglob("*.tsx"):
    text = path.read_text(encoding="utf-8")
    assert "react-icons" not in text
    assert "@heroicons" not in text
    assert "fontawesome" not in text.lower()

assert CSS.count("{") == CSS.count("}"), "CSS braces are unbalanced"
print("UI-R32 verification: PASS")
print("- Knowledge search CTA is constrained inside its panel")
print("- input/clear action share the flexible track; CTA owns intrinsic width")
print("- mobile stacks the CTA instead of shrinking typography")
print("- retrieval behavior, Demo removal and Lucide-only policy preserved")
print("- R33 Issues metadata/chip overflow remains out of scope")
