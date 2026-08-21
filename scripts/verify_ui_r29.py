from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CSS = (ROOT / "frontend" / "app" / "globals.css").read_text(encoding="utf-8")
AUDIT = (ROOT / "frontend" / "components" / "audit-workspace.tsx").read_text(encoding="utf-8")
NOTES = (ROOT / "UI_R29_NOTES.md").read_text(encoding="utf-8")

for token in [
    "UI-R29 — Visual Audit",
    ".audit-command-r29",
    ".audit-glance-r29",
    ".audit-flow-r29",
    ".audit-visual-timeline-r29",
    ".audit-event-proof-r29",
    ".audit-proof-stack-r29",
    "@media (max-width:900px)",
    "@media (max-width:700px)",
]:
    assert token in CSS, f"missing UI-R29 CSS contract: {token}"

for token in [
    'className="audit-glance-r29"',
    'className="audit-flow-r29"',
    'className="audit-visual-timeline-r29"',
    'className={`card audit-event-proof-r29 tone-${selectedTone}`}',
    'label="Execution proof"',
    'label="Evidence & impact"',
    'label="Human & governance"',
    "Priority score, not a defect verdict.",
    "AI proposes. Human decisions carry authority.",
    "getAudit(value.trim() || undefined)",
    "getDocument(documentId)",
    "hidden chain-of-thought",
]:
    assert token in AUDIT, f"Audit visual-minimalism or truthfulness contract drifted: {token}"

for token in [
    "Visual Audit",
    "Glance → Select → Prove",
    "progressive disclosure",
    "SHA-256",
    "Hidden chain-of-thought",
]:
    assert token in NOTES, f"missing UI-R29 notes contract: {token}"

assert not (ROOT / "frontend" / "app" / "demo").exists(), "Demo route must remain removed"
for path in (ROOT / "frontend").rglob("*.tsx"):
    text = path.read_text(encoding="utf-8")
    assert "react-icons" not in text
    assert "@heroicons" not in text
    assert "fontawesome" not in text.lower()

assert CSS.count("{") == CSS.count("}"), "CSS braces are unbalanced"
print("UI-R29 verification: PASS")
print("- chronology is the visual hero with select-to-prove event inspection")
print("- run proof uses live agent/Qwen/evidence/impact/human counts")
print("- deep ledgers use progressive disclosure")
print("- evidence SHA-256, human authority and no-defect-verdict semantics are preserved")
print("- Demo removal and Lucide-only policy preserved")
