from __future__ import annotations

from app.domain.models import EvidenceDocument
from app.services.configuration_facts import assess_configuration_documents


def _doc(title: str, text: str, kind: str | None = None) -> EvidenceDocument:
    return EvidenceDocument(
        id=title[:36],
        title=title,
        original_filename=f"{title}.pdf",
        document_type=kind or ("CONFIGURATION" if title.startswith("CFG-") else "TEST"),
        version="1.0",
        source="LOCAL_REPOSITORY",
        content_hash=f"hash-{title}",
        extracted_text=text,
        char_count=len(text),
        parse_status="PARSED",
    )


def test_atlas_cfg_plus_test_resolves_disabled_with_scalar_precedence():
    docs = [
        _doc(
            "CFG-ATLAS-PTP-01",
            """
            The baseline does not document an explicit duplicate-event or idempotency guard ahead of the PTP state mutation path.
            No explicit idempotency-key guard is documented in this baseline.
            """,
        ),
        _doc(
            "TEST-ATLAS-PTP-R1",
            """
            Test Result FAIL
            Recorded result: FAIL. Replaying the same accepted Promise-to-Pay event caused an additional state transition.
            CFG-ATLAS-PTP-01 records idempotency_key_required = false and duplicate_suppression = false for Atlas.
            """,
        ),
    ]

    assessment = assess_configuration_documents(docs, "duplicate_suppression")
    assert assessment.state == "DISABLED"
    assert assessment.resolution_basis == "EXPLICIT_SCALAR"
    assert assessment.conflict_reason is None
    assert assessment.warnings == []
    assert {fact.basis for fact in assessment.facts} >= {"EXPLICIT_SCALAR", "CONTROL_NARRATIVE", "TEST_ASSERTION"}
    assert any("TEST-ATLAS" in fact.source_title for fact in assessment.facts)


def test_meridian_configuration_resolves_disabled_without_test_result():
    docs = [
        _doc(
            "CFG-MERIDIAN-PTP-04",
            """
            Duplicate Suppression
            False
            This configuration does not require an idempotency key and does not enable duplicate suppression.
            """,
        ),
        _doc(
            "TEST-MERIDIAN-PTP-R1",
            """
            No dedicated duplicate replay/idempotency test is present in the current regression pack.
            Duplicate suppression is not demonstrated by current test evidence.
            """,
        ),
    ]

    assessment = assess_configuration_documents(docs, "duplicate_suppression")
    assert assessment.state == "DISABLED"
    assert assessment.resolution_basis == "EXPLICIT_SCALAR"
    assert assessment.conflict_reason is None
    assert len(assessment.supporting_document_ids) == 1


def test_nova_cfg_plus_passing_test_resolves_protected_without_fabricating_enabled():
    docs = [
        _doc(
            "CFG-NOVA-PTP-08",
            """
            Replay Protection
            Documented idempotency / duplicate-suppression protection
            Duplicate suppression
            Documented
            """,
        ),
        _doc(
            "TEST-NOVA-PTP-R1",
            """
            Test Result PASS
            Recorded result: PASS. Repository evidence records Nova Finance as having documented idempotency / duplicate-suppression protection together with a passing duplicate-replay test.
            """,
        ),
    ]

    assessment = assess_configuration_documents(docs, "duplicate_suppression")
    assert assessment.state == "PROTECTED"
    assert assessment.resolution_basis == "CONTROL_NARRATIVE"
    assert assessment.conflict_reason is None
    assert len(assessment.supporting_document_ids) == 2
    assert not any(fact.state == "ENABLED" and fact.basis == "EXPLICIT_SCALAR" for fact in assessment.facts)


def test_conflicting_explicit_scalars_fail_closed():
    docs = [
        _doc("CFG-A", "duplicate_suppression = false"),
        _doc("CFG-B", "duplicate_suppression = true"),
    ]

    assessment = assess_configuration_documents(docs, "duplicate_suppression")
    assert assessment.state == "UNKNOWN"
    assert assessment.resolution_basis == "CONFLICT"
    assert assessment.conflict_reason == "CONFLICTING_EXPLICIT_SCALARS"
    assert len(assessment.conflicting_document_ids) == 2


def test_narrative_and_runtime_divergence_without_scalar_fails_closed():
    docs = [
        _doc(
            "CFG-CLIENT-X",
            "Duplicate suppression protection is documented for the current implementation.",
        ),
        _doc(
            "TEST-CLIENT-X",
            "Recorded result: FAIL. The duplicate replay test caused an extra transition.",
        ),
    ]

    assessment = assess_configuration_documents(docs, "duplicate_suppression")
    assert assessment.state == "UNKNOWN"
    assert assessment.resolution_basis == "CONFLICT"
    assert assessment.conflict_reason == "CONFIGURATION_EXECUTION_DIVERGENCE"
    assert len(assessment.conflicting_document_ids) == 1


def test_exact_scalar_remains_authoritative_but_surfaces_lower_tier_divergence():
    docs = [
        _doc("CFG-CLIENT-X", "duplicate_suppression = false"),
        _doc(
            "TEST-CLIENT-X",
            "Recorded result: PASS. The duplicate replay test passed and replay protection prevented another state mutation.",
        ),
    ]

    assessment = assess_configuration_documents(docs, "duplicate_suppression")
    assert assessment.state == "DISABLED"
    assert assessment.resolution_basis == "EXPLICIT_SCALAR"
    assert assessment.warnings == ["LOWER_TIER_SIGNAL_DIVERGENCE"]
    assert len(assessment.conflicting_document_ids) == 1


def test_no_supported_fact_remains_unknown():
    docs = [_doc("CFG-OTHER", "This record only documents settlement windows.")]
    assessment = assess_configuration_documents(docs, "duplicate_suppression")
    assert assessment.state == "UNKNOWN"
    assert assessment.resolution_basis == "NO_EVIDENCE"
    assert assessment.conflict_reason == "NO_CONFIGURATION_FACTS"
