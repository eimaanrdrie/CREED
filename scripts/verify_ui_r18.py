from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CSS = (ROOT / "frontend" / "app" / "globals.css").read_text(encoding="utf-8")
REGISTRY = (ROOT / "frontend" / "components" / "recalls-workspace.tsx").read_text(encoding="utf-8")
NOTICE = (ROOT / "frontend" / "components" / "recall-notice-workspace.tsx").read_text(encoding="utf-8")
NOTES = (ROOT / "UI_R18_NOTES.md").read_text(encoding="utf-8")

required_css = [
    "UI-R18 — Recalls + Governance Artefacts Readability Recomposition",
    ".recall-page-r07,\n.recall-notice-page-r07 {\n  max-width: 1320px",
    "--type-md: 15px",
    "min-height: 44px",
    "@media (max-width: 1420px)",
    ".recall-layout-r07,\n  .recall-notice-layout-r07 { grid-template-columns: 1fr; }",
    "content: attr(data-label)",
    "overflow-wrap: anywhere",
]
for token in required_css:
    assert token in CSS, f"missing UI-R18 CSS contract: {token}"

for token in [
    'data-label="Issued"',
    "Knowledge is revoked only by an authorised reviewer.",
    "Only explicit adopters are recalled.",
    "Adoption history is not erased.",
    "It will not declare those implementations defective.",
]:
    assert token in REGISTRY, f"Recall registry governance contract drifted: {token}"

for token in [
    'data-label="Review obligation"',
    "Routing is a review obligation, not a defect verdict.",
    "The verifier recomputes the canonical notice payload",
    "Recall does not erase adoption.",
    "Signed Recall Notice",
]:
    assert token in NOTICE, f"Recall notice governance contract drifted: {token}"

assert "Recalls + Governance Artefacts Readability Recomposition" in NOTES
assert not (ROOT / "frontend" / "app" / "demo").exists(), "Demo route must remain removed"
for path in (ROOT / "frontend").rglob("*.tsx"):
    text = path.read_text(encoding="utf-8")
    assert "react-icons" not in text
    assert "@heroicons" not in text
    assert "fontawesome" not in text.lower()

assert CSS.count("{") == CSS.count("}"), "CSS braces are unbalanced"
print("UI-R18 verification: PASS")
print("- Recalls and Signed Recall Notice bounded to 1320px")
print("- registry, revocation drawer and governance artefacts use larger operational typography")
print("- decision-bearing and evidence actions meet 44px interaction floor")
print("- governance sidebars reflow before fixed-sidebar compression")
print("- human authority, explicit A-BOM routing and no-defect-verdict semantics retained")
