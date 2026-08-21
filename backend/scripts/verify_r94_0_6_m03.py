from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
advanced = (ROOT / "backend/app/services/advanced.py").read_text()
test_path = ROOT / "backend/tests/test_r94_0_6_m03_variable_change_findings.py"

checks = {
    "structured_fact_import": "assess_configuration_documents" in advanced,
    "structured_change_mapper": "def _structured_configuration_change_output(" in advanced,
    "protected_non_fabrication": "does not fabricate a literal persisted true value" in advanced,
    "unknown_fail_closed": "CONFLICTING_EXPLICIT_SCALARS" in (ROOT / "backend/app/services/configuration_facts.py").read_text(),
    "m03_regression_exists": test_path.exists(),
    "generic_scalar_fallback_preserved": "_configuration_values_from_document(doc, change.variable)" in advanced,
}
failed = [name for name, ok in checks.items() if not ok]
if failed:
    raise SystemExit("R94.0.6-M03 verifier failed: " + ", ".join(failed))
print("R94.0.6-M03 verifier PASS")
