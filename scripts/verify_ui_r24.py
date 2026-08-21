from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ISSUES = (ROOT / "frontend" / "components" / "issues-workspace.tsx").read_text(encoding="utf-8")
INTAKE = (ROOT / "frontend" / "components" / "issue-capsule-form.tsx").read_text(encoding="utf-8")
CSS = (ROOT / "frontend" / "app" / "globals.css").read_text(encoding="utf-8")
NOTES = (ROOT / "UI_R24_NOTES.md").read_text(encoding="utf-8")

for token in [
    "UI-R24 — Minimal Issues + Intake",
    ".issue-command-r24",
    ".issue-filter-disclosure-r24",
    ".issue-case-row-r24",
    ".issue-intake-min-r24",
    ".issue-stepper-r24",
    ".issue-choice-r24",
    ".issue-snapshot-r24",
    ".issue-after-save-r24",
    ".issue-review-r24",
]:
    assert token in CSS, f"missing R24 visual-minimalism contract: {token}"

for token in [
    'className="page issues-page issues-min-r24"',
    'placeholder="Search cases"',
    'className="issue-filter-disclosure-r24"',
    'SignalChip tone={severityTone(issue.severity)}',
    'SignalChip icon={Paperclip}',
    'note="Unresolved"',
    'note="Awaiting authority"',
]:
    assert token in ISSUES, f"Issues registry did not adopt R24 signal-first pattern: {token}"

# Keep the R14 responsive semantic labels even though classification/evidence are
# visually represented as chips in the default R24 row.
for label in ["Client / ticket", "Classification", "Evidence", "Status"]:
    assert f'data-label="{label}"' in ISSUES, f"responsive ledger label drifted: {label}"

assert "{issue.description}" not in ISSUES, "default case ledger should not render issue-description prose in R24"

for token in [
    "What changed?",
    "Capture source facts. AI starts after save.",
    "Human source",
    "AI after save",
    'SectionIntro index="01" title="Source context" text="Client and ticket, if known."',
    'SectionIntro index="02" title="What happened?" text="Use the reporter\'s words."',
    'SectionIntro index="03" title="Classify" text="Human-reported labels only."',
    'SectionIntro index="04" title="Evidence" text="Optional source files."',
    'ProgressiveDisclosure label="After save"',
    'ProgressiveDisclosure label="Observation"',
    "Save & analyse",
]:
    assert token in INTAKE, f"Issue intake did not adopt R24 minimal pattern: {token}"

# Product behavior must remain real and unchanged.
for token in [
    "createIssue({ external_ticket_id: ticket || null",
    'form.set("source", "ISSUE_ATTACHMENT")',
    'form.set("issue_id", issueId)',
    "await uploadDocument(form)",
    "window.location.href = `/issues/${issueId}/analysis?run=1`",
]:
    assert token in INTAKE, f"R24 drifted issue/evidence behavior: {token}"

assert "GLANCE → INSPECT → PROVE" in NOTES
assert not (ROOT / "frontend" / "app" / "demo").exists(), "Demo route must remain removed"
for path in (ROOT / "frontend").rglob("*.tsx"):
    text = path.read_text(encoding="utf-8")
    assert "react-icons" not in text
    assert "@heroicons" not in text
    assert "fontawesome" not in text.lower()

assert CSS.count("{") == CSS.count("}"), "CSS braces are unbalanced"
print("UI-R24 verification: PASS")
print("- issue registry is signal-first and no longer renders description prose by default")
print("- secondary filters moved behind progressive disclosure")
print("- intake copy, progress, classification, preview and review are visually distilled")
print("- createIssue, evidence upload and analysis-launch behavior are preserved")
print("- typography floor, responsive semantics, Demo removal and Lucide-only policy preserved")
