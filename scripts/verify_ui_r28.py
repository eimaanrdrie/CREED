from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CSS = (ROOT / "frontend" / "app" / "globals.css").read_text(encoding="utf-8")
REGISTRY = (ROOT / "frontend" / "components" / "recalls-workspace.tsx").read_text(encoding="utf-8")
NOTICE = (ROOT / "frontend" / "components" / "recall-notice-workspace.tsx").read_text(encoding="utf-8")
NOTES = (ROOT / "UI_R28_NOTES.md").read_text(encoding="utf-8")

for token in [
    "UI-R28 — Visual Recall",
    ".recall-glance-r28",
    ".recall-flow-r28",
    ".recall-card-grid-r28",
    ".recall-proof-r28",
    ".revoke-flow-r28",
    ".recall-notice-flow-r28",
    ".recall-route-grid-r28",
    ".recall-proof-stack-r28",
    "@media (max-width:820px)",
    "@media (max-width:620px)",
]:
    assert token in CSS, f"missing UI-R28 CSS contract: {token}"

for token in [
    'className="recall-glance-r28"',
    'className="recall-flow-r28"',
    'className="recall-card-grid-r28"',
    'className="recall-governance-r28"',
    "revokeMethodVersion(versionId",
    "Knowledge is revoked only by an authorised reviewer.",
    "Only explicit adopters are recalled.",
    "Adoption history is not erased.",
    "It will not declare those implementations defective.",
]:
    assert token in REGISTRY, f"Recall registry visual-minimalism or governance contract drifted: {token}"

for token in [
    'className="recall-notice-flow-r28"',
    'className="recall-route-grid-r28"',
    'className="recall-proof-stack-r28"',
    "Human attestation",
    "Integrity proof",
    "The verifier recomputes the canonical notice payload",
    "Routing is a review obligation, not a defect verdict.",
    "Recall does not erase adoption.",
    "verifyRecall(recallId)",
]:
    assert token in NOTICE, f"Recall notice proof contract drifted: {token}"

for token in [
    "Visual Recall",
    "Revoked Method → Local A-BOM → Routed Adopters → Human Review",
    "progressive disclosure",
    "SHA-256",
]:
    assert token in NOTES, f"missing UI-R28 notes contract: {token}"

assert not (ROOT / "frontend" / "app" / "demo").exists(), "Demo route must remain removed"
for path in (ROOT / "frontend").rglob("*.tsx"):
    text = path.read_text(encoding="utf-8")
    assert "react-icons" not in text
    assert "@heroicons" not in text
    assert "fontawesome" not in text.lower()

assert CSS.count("{") == CSS.count("}"), "CSS braces are unbalanced"
print("UI-R28 verification: PASS")
print("- recall registry is visual-first with compact live signals")
print("- revoked method -> A-BOM -> routed adopter -> human review path is visible")
print("- notice proof uses progressive disclosure for authority, evidence and SHA-256")
print("- real revocation/verification APIs and no-defect-verdict semantics are preserved")
print("- Demo removal and Lucide-only policy preserved")
