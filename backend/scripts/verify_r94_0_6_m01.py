from pathlib import Path

root = Path(__file__).resolve().parents[2]
service = root / "backend/app/services/configuration_facts.py"
test = root / "backend/tests/test_r94_0_6_m01_structured_configuration_facts.py"

assert service.exists(), "configuration_facts.py missing"
assert test.exists(), "M01 regression test missing"
text = service.read_text()
for token in [
    'class ConfigurationFact',
    '"EXPLICIT_SCALAR"',
    '"CONTROL_NARRATIVE"',
    '"TEST_ASSERTION"',
    '"PROTECTED"',
    'def extract_configuration_facts',
]:
    assert token in text, f"missing source contract: {token}"
print("PASS: R94.0.6-M01 structured configuration fact extraction contract present")
