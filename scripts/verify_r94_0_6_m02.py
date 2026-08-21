from pathlib import Path

root = Path(__file__).resolve().parents[1]
service = (root / "backend/app/services/configuration_facts.py").read_text()
tests = (root / "backend/tests/test_r94_0_6_m02_configuration_fact_aggregation.py").read_text()

required_service = [
    "class ConfigurationFactAssessment",
    "def aggregate_configuration_facts",
    "def assess_configuration_documents",
    '"CONFLICTING_EXPLICIT_SCALARS"',
    '"CONFIGURATION_EXECUTION_DIVERGENCE"',
    '"LOWER_TIER_SIGNAL_DIVERGENCE"',
    'resolution_basis="EXPLICIT_SCALAR"',
    'resolution_basis="CONTROL_NARRATIVE"',
    'resolution_basis="TEST_ASSERTION"',
]
for marker in required_service:
    assert marker in service, marker

required_tests = [
    "test_atlas_cfg_plus_test_resolves_disabled_with_scalar_precedence",
    "test_meridian_configuration_resolves_disabled_without_test_result",
    "test_nova_cfg_plus_passing_test_resolves_protected_without_fabricating_enabled",
    "test_conflicting_explicit_scalars_fail_closed",
    "test_narrative_and_runtime_divergence_without_scalar_fails_closed",
]
for marker in required_tests:
    assert marker in tests, marker

# M02 must not silently wire itself into Investigation before the next approved module.
advanced = (root / "backend/app/services/advanced.py").read_text()
assert "assess_configuration_documents(" not in advanced

print("R94.0.6-M02 source verifier: PASS")
