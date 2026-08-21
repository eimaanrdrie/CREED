from pathlib import Path

root = Path(__file__).resolve().parents[1]
advanced = (root / "backend/app/services/advanced.py").read_text()
api = (root / "backend/app/api/advanced.py").read_text()
ui = (root / "frontend/components/analysis-shell.tsx").read_text()
css = (root / "frontend/app/globals.css").read_text()

for term in [
    "def assess_human_decision_consistency",
    "CONTRADICTS_TECHNICAL_ADVISORY",
    "R9406_CONTRADICTION_RATIONALE_MIN_CHARS = 24",
    '"requires_explicit_rationale"',
]:
    assert term in advanced, term

for term in [
    "TECHNICAL_ADVISORY_CONTRADICTION_RATIONALE_REQUIRED",
    "decision_consistency",
    "assess_human_decision_consistency",
]:
    assert term in api, term

for term in [
    "TECHNICAL ADVISORY CONTRADICTION",
    "RECORDED TECHNICAL EXCEPTION",
    "Human Authority may still proceed",
    "reviewDraftReady",
    "decision_consistency",
]:
    assert term in ui, term

assert ".decision-consistency-warning-r9406" in css
assert ".technical-exception-r9406" in css
print("R94.0.6-M06 source verifier PASS")
