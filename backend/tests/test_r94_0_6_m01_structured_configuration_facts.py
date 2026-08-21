from __future__ import annotations

from app.domain.models import EvidenceDocument
from app.services.configuration_facts import extract_configuration_facts


def _doc(title: str, text: str) -> EvidenceDocument:
    return EvidenceDocument(
        title=title,
        original_filename=f"{title}.pdf",
        document_type="CONFIGURATION" if title.startswith("CFG-") else "TEST",
        version="1.0",
        source="LOCAL_REPOSITORY",
        content_hash=f"hash-{title}",
        extracted_text=text,
        char_count=len(text),
        parse_status="PARSED",
    )


def test_atlas_cross_document_wording_extracts_disabled_facts_without_inventing_true_false():
    cfg = _doc(
        "CFG-ATLAS-PTP-01",
        """
        Configuration boundary. This record documents the Atlas implementation baseline for PTP-EVENT-v1.
        The baseline does not document an explicit duplicate-event or idempotency guard ahead of the PTP state mutation path.
        Duplicate-event boundary
        No explicit idempotency-key guard is documented in this baseline.
        """,
    )
    test = _doc(
        "TEST-ATLAS-PTP-R1",
        """
        Test Result
        FAIL
        Recorded result: FAIL. Replaying the same accepted Promise-to-Pay event caused an additional state transition.
        CFG-ATLAS-PTP-01 records idempotency_key_required = false and duplicate_suppression = false for Atlas.
        """,
    )

    cfg_facts = extract_configuration_facts(cfg, "duplicate_suppression")
    test_facts = extract_configuration_facts(test, "duplicate_suppression")

    assert any(f.state == "DISABLED" and f.basis == "CONTROL_NARRATIVE" for f in cfg_facts)
    assert any(f.state == "DISABLED" and f.basis == "EXPLICIT_SCALAR" and f.raw_value.lower() == "false" for f in test_facts)
    assert any(f.state == "DISABLED" and f.basis == "TEST_ASSERTION" and f.raw_value == "FAIL" for f in test_facts)


def test_meridian_table_and_narrative_extract_explicit_disabled_state():
    doc = _doc(
        "CFG-MERIDIAN-PTP-04",
        """
        Idempotency Key Required

        False

        Duplicate Suppression

        False

        This configuration does not require an idempotency key and does not enable duplicate suppression.
        Duplicate suppression
        False
        A duplicate-suppression control is not enabled by this configuration.
        """,
    )

    facts = extract_configuration_facts(doc, "duplicate_suppression")
    assert any(f.state == "DISABLED" and f.basis == "EXPLICIT_SCALAR" for f in facts)
    assert any(f.state == "DISABLED" and f.basis == "CONTROL_NARRATIVE" for f in facts)


def test_nova_documented_control_is_protected_not_fabricated_literal_true():
    cfg = _doc(
        "CFG-NOVA-PTP-08",
        """
        Replay Protection
        Documented idempotency / duplicate-suppression protection

        Duplicate suppression
        Documented

        Repository configuration evidence identifies duplicate-suppression protection.
        """,
    )
    test = _doc(
        "TEST-NOVA-PTP-R1",
        """
        Test Result
        PASS
        Recorded result: PASS. Repository evidence records Nova Finance as having documented idempotency / duplicate-suppression protection together with a passing duplicate-replay test.
        """,
    )

    cfg_facts = extract_configuration_facts(cfg, "duplicate_suppression")
    test_facts = extract_configuration_facts(test, "duplicate_suppression")

    assert any(f.state == "PROTECTED" and f.basis == "CONTROL_NARRATIVE" for f in cfg_facts)
    assert not any(f.state == "ENABLED" and f.basis == "EXPLICIT_SCALAR" for f in cfg_facts)
    assert any(f.state == "PROTECTED" and f.basis == "TEST_ASSERTION" and f.raw_value == "PASS" for f in test_facts)


def test_exact_scalar_true_is_still_extracted_as_enabled():
    doc = _doc("CFG-GENERIC", "duplicate_suppression = true")
    facts = extract_configuration_facts(doc, "duplicate_suppression")
    assert len(facts) == 1
    assert facts[0].state == "ENABLED"
    assert facts[0].basis == "EXPLICIT_SCALAR"
    assert facts[0].confidence == 1.0


def test_unrelated_document_returns_no_fact_instead_of_guessing():
    doc = _doc("CFG-OTHER", "This document describes batch scheduling and settlement windows only.")
    assert extract_configuration_facts(doc, "duplicate_suppression") == []
