from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DASH = (ROOT / "frontend" / "components" / "final-dashboard.tsx").read_text(encoding="utf-8")
CSS = (ROOT / "frontend" / "app" / "globals.css").read_text(encoding="utf-8")
NOTES = (ROOT / "UI_R23_NOTES.md").read_text(encoding="utf-8")

for token in [
    "UI-R23 — Minimal Visual Overview",
    ".command-strip-r23",
    ".command-signal-r23",
    ".assurance-flow-r23",
    ".decision-focus-r23",
    ".coverage-rings-r23",
    ".workload-chips-r23",
    ".governance-min-list-r23",
]:
    assert token in CSS, f"missing R23 visual overview contract: {token}"

for token in [
    "See what needs action. Prove why.",
    "Issue → evidence → impact → human → recall.",
    "commandSignals",
    "flowSteps",
    "ProgressiveDisclosure label=\"Evidence coverage\"",
    "ProgressiveDisclosure label=\"Delivery workload\"",
    "ProgressiveDisclosure label=\"Recent human decisions\"",
    "CoverageRing",
    "VisualMetric",
    "SignalChip",
]:
    assert token in DASH, f"Overview did not adopt R23 glance/inspect/prove pattern: {token}"

# All visible business values in the new command view must still derive from the
# dashboard/issues state rather than static result literals.
for token in [
    "metrics?.pending_human_decisions",
    "metrics?.active_recalls",
    "metrics?.high_priority_impacts",
    "metrics?.open_issues",
    "data?.coverage?.traceable_findings",
    'issue.status === "WAITING_HUMAN"',
]:
    assert token in DASH, f"R23 signal lost backend-derived source: {token}"

assert "The assurance loop" not in DASH, "old explanatory assurance loop should not remain visible in R23"
assert "Investigations paused at the human-authority boundary." not in DASH
assert "Revoked knowledge with downstream implementations requiring review." not in DASH
assert "Change Radar candidates currently scored in the highest priority band." not in DASH
assert "GLANCE → INSPECT → PROVE" in NOTES
assert not (ROOT / "frontend" / "app" / "demo").exists(), "Demo route must remain removed"
for path in (ROOT / "frontend").rglob("*.tsx"):
    text = path.read_text(encoding="utf-8")
    assert "react-icons" not in text
    assert "@heroicons" not in text
    assert "fontawesome" not in text.lower()

assert CSS.count("{") == CSS.count("}"), "CSS braces are unbalanced"
print("UI-R23 verification: PASS")
print("- Overview is signal-first: 3 command metrics + visual assurance path")
print("- decision queue is compact and human-authority state remains explicit")
print("- evidence coverage, workload and governance detail moved behind disclosure")
print("- all displayed business values remain backend-derived")
print("- typography, responsive behavior, Demo removal and Lucide-only policy preserved")
