from __future__ import annotations

from app.domain.models import EvidenceDocument, SupportIssue
from app.services.advanced import (
    _configuration_change_investigation_output,
    _configuration_values_from_document,
    _extract_configuration_change_request,
)
from app.services.configuration_facts import extract_configuration_facts
from test_r94_0_6_m03_variable_change_findings import _doc, _impl


def _issue(description: str, title: str = "Configuration change request") -> SupportIssue:
    return SupportIssue(
        id="issue-m07",
        external_ticket_id="SUP-M07",
        title=title,
        description=description,
        issue_type="CHANGE_REQUEST",
        severity="HIGH",
        status="OPEN",
    )


def test_boolean_aliases_and_separator_variants_resolve_without_qwen():
    cases = [
        ("Set `duplicate_suppression` from off to on.", "duplicate_suppression: off"),
        ("Change `duplicate_suppression` from disabled to enabled.", "Duplicate Suppression\nDisabled"),
        ("Set `duplicate-suppression` false -> true.", "duplicate-suppression = false"),
        ("Update `duplicate.suppression` from false to true.", "duplicate.suppression: false"),
    ]
    for description, text in cases:
        issue = _issue(description)
        change = _extract_configuration_change_request(issue)
        assert change is not None
        assert change.variable == "duplicate_suppression"
        assert change.requested_value == "true"

        doc = _doc("CFG-M07", text)
        facts = extract_configuration_facts(doc, "duplicate_suppression")
        assert any(fact.state == "DISABLED" and fact.basis == "EXPLICIT_SCALAR" for fact in facts)

        out = _configuration_change_investigation_output(issue, _impl(), None, [doc])
        assert out is not None
        assert out.finding_type == "POTENTIALLY_AFFECTED"
        assert out.configuration_comparison is not None
        assert out.configuration_comparison.technical_result == "CHANGE_REVIEW_REQUIRED"


def test_numeric_scalars_support_ini_yaml_pdf_table_and_numeric_equivalence():
    issue = _issue("Change `retry_window_seconds` from 30 to 60.")
    formats = [
        "retry_window_seconds = 30",
        "retry_window_seconds: 30",
        "Retry Window Seconds\n30",
        "Retry Window Seconds 30",
    ]
    for text in formats:
        doc = _doc("CFG-RETRY", text)
        assert _configuration_values_from_document(doc, "retry_window_seconds") == ["30"]
        out = _configuration_change_investigation_output(issue, _impl(), None, [doc])
        assert out is not None
        assert out.finding_type == "POTENTIALLY_AFFECTED"
        assert "requested value is 60" in out.statement

    already = _doc("CFG-RETRY-MATCH", "retry_window_seconds: 60.0")
    out = _configuration_change_investigation_output(issue, _impl(), None, [already])
    assert out is not None
    assert out.finding_type == "NO_SUPPORTING_EVIDENCE_OF_IMPACT"


def test_string_scalar_change_preserves_exact_string_semantics_and_quotes():
    issue = _issue("Change `retry_policy` from `linear` to `exponential`.")
    doc = _doc("CFG-POLICY", 'retry_policy: "linear"')
    assert _configuration_values_from_document(doc, "retry_policy") == ["linear"]
    out = _configuration_change_investigation_output(issue, _impl(), None, [doc])
    assert out is not None
    assert out.finding_type == "POTENTIALLY_AFFECTED"

    matching = _doc("CFG-POLICY-MATCH", "Retry Policy\nexponential")
    out = _configuration_change_investigation_output(issue, _impl(), None, [matching])
    assert out is not None
    assert out.finding_type == "NO_SUPPORTING_EVIDENCE_OF_IMPACT"


def test_equivalent_numeric_values_do_not_create_false_authoritative_conflict():
    issue = _issue("Change `retry_window_seconds` from 30 to 60.")
    docs = [
        _doc("CFG-A", "retry_window_seconds = 30"),
        _doc("CFG-B", "retry_window_seconds: 30.0"),
    ]
    out = _configuration_change_investigation_output(issue, _impl(), None, docs)
    assert out is not None
    assert out.finding_type == "POTENTIALLY_AFFECTED"
    assert "conflicting values" not in out.statement


def test_real_non_equivalent_scalar_conflict_remains_insufficient_evidence():
    issue = _issue("Change `retry_window_seconds` from 30 to 60.")
    docs = [
        _doc("CFG-A", "retry_window_seconds = 30"),
        _doc("CFG-B", "retry_window_seconds = 45"),
    ]
    out = _configuration_change_investigation_output(issue, _impl(), None, docs)
    assert out is not None
    assert out.finding_type == "INSUFFICIENT_EVIDENCE"
    assert "conflicting values" in out.statement


def test_missing_scalar_evidence_falls_back_instead_of_fabricating_a_value():
    issue = _issue("Change `retry_window_seconds` from 30 to 60.")
    doc = _doc("CFG-NO-VALUE", "Retry behavior is reviewed by operations.")
    out = _configuration_change_investigation_output(issue, _impl(), None, [doc])
    assert out is None


def test_vague_issue_without_requested_value_does_not_activate_deterministic_comparator():
    issue = _issue("Please review `duplicate_suppression` behavior across registered implementations.")
    assert _extract_configuration_change_request(issue) is None


def test_parser_accepts_dotted_key_with_explicit_set_to_target():
    issue = _issue("Configure `ptp.retry_window_seconds` to 60 for this bank.")
    change = _extract_configuration_change_request(issue)
    assert change is not None
    assert change.variable == "ptp_retry_window_seconds"
    assert change.requested_value == "60"
