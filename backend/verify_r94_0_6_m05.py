from pathlib import Path

root = Path(__file__).resolve().parents[1]
advanced = (root / "backend/app/services/advanced.py").read_text()
api = (root / "backend/app/api/advanced.py").read_text()
ui = (root / "frontend/components/analysis-shell.tsx").read_text()
css = (root / "frontend/app/globals.css").read_text()

for term in [
    "def build_configuration_change_summary",
    '"change_required_count"',
    '"remediation_targets"',
    '"already_protected"',
    '"reconciliation_targets"',
]:
    assert term in advanced, term

for term in [
    "configuration_change_summary",
    "client_name':client.name",
]:
    assert term in api, term

for term in [
    "CROSS-BANK CHANGE SUMMARY",
    "implementation",
    "require change",
    "Remediation targets are derived from persisted candidate evidence",
    "CrossBankConfigurationSummary",
]:
    assert term in ui, term

assert ".cross-bank-change-summary-r9406" in css
print("R94.0.6-M05 source verifier PASS")
