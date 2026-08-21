from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
advanced = (ROOT / "backend/app/services/advanced.py").read_text()
facts = (ROOT / "backend/app/services/configuration_facts.py").read_text()
test = (ROOT / "backend/tests/test_r94_0_6_m07_variable_change_robustness.py").read_text()

required_advanced = [
    "def _configuration_key_pattern",
    "(?:->|→)",
    "def _simple_configuration_scalar",
    "def _configuration_value_key",
    "Decimal(normalized)",
    "key=value``, ``key: value",
    "_configuration_value_key(current_value) != _configuration_value_key(requested_value)",
]
required_facts = [
    "(?:=|:)",
    "snake_case, kebab-case and dotted label forms",
]
required_tests = [
    "test_boolean_aliases_and_separator_variants_resolve_without_qwen",
    "test_numeric_scalars_support_ini_yaml_pdf_table_and_numeric_equivalence",
    "test_string_scalar_change_preserves_exact_string_semantics_and_quotes",
    "test_real_non_equivalent_scalar_conflict_remains_insufficient_evidence",
    "test_missing_scalar_evidence_falls_back_instead_of_fabricating_a_value",
]

for token in required_advanced:
    if token not in advanced:
        raise SystemExit(f"FAIL advanced.py missing: {token}")
for token in required_facts:
    if token not in facts:
        raise SystemExit(f"FAIL configuration_facts.py missing: {token}")
for token in required_tests:
    if token not in test:
        raise SystemExit(f"FAIL M07 tests missing: {token}")
print("R94.0.6-M07 source verifier PASS")
