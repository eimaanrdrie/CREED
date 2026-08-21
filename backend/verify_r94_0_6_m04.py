from pathlib import Path

root = Path(__file__).resolve().parents[1]
advanced = (root / "backend/app/services/advanced.py").read_text()
api = (root / "backend/app/api/advanced.py").read_text()
ui = (root / "frontend/components/analysis-shell.tsx").read_text()
css = (root / "frontend/app/globals.css").read_text()

required_backend = [
    "class ConfigurationComparison(BaseModel)",
    "configuration_comparison: ConfigurationComparison | None = None",
    'technical_result="CHANGE_REVIEW_REQUIRED"',
    '"ALREADY_PROTECTED"',
    'technical_result="EVIDENCE_RECONCILIATION_REQUIRED"',
]
for term in required_backend:
    assert term in advanced, term
assert "configuration_comparison':comparison" in api

required_ui = [
    "CONFIGURATION CHANGE ANALYSIS",
    "Current state",
    "Requested state",
    "CHANGE REQUIRED",
    "ALREADY PROTECTED",
    "Human Authority remains the final decision",
]
for term in required_ui:
    assert term in ui, term
assert ".configuration-comparison-r9406" in css
print("R94.0.6-M04 source verifier PASS")
