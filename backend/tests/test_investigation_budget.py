from app.services.advanced import InvestigationModelOutput, InvestigationOutput, _complete_statement, _investigation_format_schema


def test_investigation_schema_bounds_output_and_citations():
    schema = _investigation_format_schema(["DOC-A", "DOC-B", "DOC-C"])

    assert schema["properties"]["statement"]["maxLength"] == 420
    assert schema["properties"]["evidence"]["maxItems"] == 2
    assert schema["properties"]["evidence"]["items"]["enum"] == [1, 2]
    assert schema["properties"]["missing"]["maxItems"] == 2

    parsed = InvestigationModelOutput.model_validate(
        {"finding": "INSUFFICIENT_EVIDENCE", "statement": "Evidence is incomplete.", "confidence": 0.4, "evidence": [1], "missing": []}
    )
    assert parsed.evidence == [1]


def test_investigation_output_rejects_oversized_results():
    data = {
        "finding_type": "INSUFFICIENT_EVIDENCE",
        "statement": "Evidence is incomplete.",
        "confidence": 0.4,
        "evidence_ids": ["DOC-A", "DOC-B", "DOC-C"],
        "evidence_observations": [],
        "missing_evidence": [],
    }

    try:
        InvestigationOutput.model_validate(data)
    except ValueError:
        pass
    else:
        raise AssertionError("Investigation output accepted more than two evidence IDs")


def test_incomplete_model_suffix_is_removed_without_adding_facts():
    text = "The evidence does not contain audit-log data. A configuration flag alone cannot establish whether"

    assert _complete_statement(text) == "The evidence does not contain audit-log data."
    assert _complete_statement("Evidence is incomplete") == "Evidence is incomplete."
