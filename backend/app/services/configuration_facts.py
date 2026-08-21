from __future__ import annotations

import re
from typing import Literal

from pydantic import BaseModel, Field

from app.domain.models import EvidenceDocument


FactState = Literal["ENABLED", "DISABLED", "PROTECTED", "UNKNOWN"]
FactBasis = Literal[
    "EXPLICIT_SCALAR",
    "CONTROL_NARRATIVE",
    "TEST_ASSERTION",
]


class ConfigurationFact(BaseModel):
    """One source-grounded configuration/control fact extracted from one document.

    R94.0.6-M01 intentionally does not aggregate facts or decide impact.  It only
    normalizes source language into a typed, auditable representation so later
    modules can combine CFG and TEST evidence without asking Qwen to guess a
    scalar value from prose.
    """

    variable: str
    state: FactState
    basis: FactBasis
    source_document_id: str
    source_title: str
    raw_value: str | None = None
    evidence_text: str = Field(min_length=3, max_length=360)
    confidence: float = Field(ge=0.0, le=1.0)


def normalize_configuration_key(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", str(value).strip().lower()).strip("_")


def _normalized_scalar(value: str) -> FactState | None:
    lowered = str(value).strip().strip("`'\" ").rstrip(".,;:").lower()
    if lowered in {"true", "yes", "on", "enabled", "enable", "1"}:
        return "ENABLED"
    if lowered in {"false", "no", "off", "disabled", "disable", "0"}:
        return "DISABLED"
    return None


def _compact_excerpt(text: str, start: int, end: int, radius: int = 120) -> str:
    left = max(0, start - radius)
    right = min(len(text), end + radius)
    compact = " ".join(text[left:right].split())
    return compact[:360]


def _append_unique(facts: list[ConfigurationFact], fact: ConfigurationFact) -> None:
    signature = (fact.variable, fact.state, fact.basis, fact.source_document_id, fact.raw_value)
    if any(
        (item.variable, item.state, item.basis, item.source_document_id, item.raw_value) == signature
        for item in facts
    ):
        return
    facts.append(fact)


def extract_configuration_facts(doc: EvidenceDocument, variable: str) -> list[ConfigurationFact]:
    """Extract conservative structured facts for ``variable`` from one document.

    Supported evidence forms deliberately match the real CREED demo repository:
    explicit key/value assignments, PDF table-style key/value text, qualitative
    control narratives, and replay-regression outcomes.  PROTECTED is kept
    distinct from literal ENABLED so later modules never fabricate ``true`` when
    the source only documents a protective control.
    """

    target = normalize_configuration_key(variable)
    if not target:
        return []

    text = doc.extracted_text or ""
    lowered = text.lower()
    title = str(doc.title or doc.original_filename or doc.id)
    facts: list[ConfigurationFact] = []

    # 1) Explicit scalar assignment: duplicate_suppression = false / true.
    #    Match the requested key directly so the assignment can appear inside prose
    #    (as it does in TEST-ATLAS-PTP-R1), not only as a standalone line.
    key_pattern = r"[_\s.\-]+".join(re.escape(part) for part in target.split("_") if part)
    assignment = re.compile(
        rf"(?i)\b{key_pattern}\b\s*(?:=|:)\s*[`'\"]?([A-Za-z0-9_.\-]+)[`'\"]?"
    )
    for match in assignment.finditer(text):
        raw = match.group(1).strip()
        state = _normalized_scalar(raw)
        if not state:
            continue
        _append_unique(
            facts,
            ConfigurationFact(
                variable=target,
                state=state,
                basis="EXPLICIT_SCALAR",
                source_document_id=str(doc.id),
                source_title=title,
                raw_value=raw,
                evidence_text=_compact_excerpt(text, match.start(), match.end()),
                confidence=1.0,
            ),
        )

    # 2) PDF/table extraction often separates a label and its value by blank lines.
    #    Example from CFG-MERIDIAN-PTP-04: "Duplicate Suppression\n\nFalse".
    # Accept human-readable, snake_case, kebab-case and dotted label forms.
    # PDF extraction frequently rewrites separators, so the same normalized key
    # must survive those presentation differences without fuzzy key invention.
    table_pattern = re.compile(
        rf"(?is)\b{key_pattern}\b\s*(?:[:=\-]?\s*)?(true|false|enabled|disabled|yes|no|on|off)\b"
    )
    for match in table_pattern.finditer(text):
        raw = match.group(1)
        state = _normalized_scalar(raw)
        if not state:
            continue
        _append_unique(
            facts,
            ConfigurationFact(
                variable=target,
                state=state,
                basis="EXPLICIT_SCALAR",
                source_document_id=str(doc.id),
                source_title=title,
                raw_value=raw,
                evidence_text=_compact_excerpt(text, match.start(), match.end()),
                confidence=0.99,
            ),
        )

    # 3) Control narratives.  These are semantic control-state facts, not fabricated
    #    literal scalars.  They intentionally remain distinct from EXPLICIT_SCALAR.
    narrative_patterns: list[tuple[re.Pattern[str], FactState, float]] = [
        (
            re.compile(r"(?is)\bdoes\s+not\s+enable\s+duplicate[\s\-_]+suppression\b"),
            "DISABLED",
            0.96,
        ),
        (
            re.compile(r"(?is)\bduplicate[\s\-_]+suppression\s+(?:control\s+)?is\s+not\s+enabled\b"),
            "DISABLED",
            0.96,
        ),
        (
            re.compile(r"(?is)\bno\s+explicit\s+(?:duplicate[\s\-_]+event\s+or\s+)?idempotency(?:[\s\-_]+key)?\s+guard\b"),
            "DISABLED",
            0.80,
        ),
        (
            re.compile(r"(?is)\bdoes\s+not\s+document\s+an?\s+explicit\s+duplicate[\s\-_]+event\s+or\s+idempotency(?:[\s\-_]+key)?\s+guard\b"),
            "DISABLED",
            0.80,
        ),
        (
            re.compile(r"(?is)\bduplicate[\s\-_]+suppression\s*(?:\n|\r|\s)+documented\b"),
            "PROTECTED",
            0.90,
        ),
        (
            re.compile(r"(?is)\bdocumented\s+idempotency\s*/\s*duplicate[\s\-_]+suppression\s+protection\b"),
            "PROTECTED",
            0.92,
        ),
        (
            re.compile(r"(?is)\bduplicate[\s\-_]+suppression\s+protection\s+(?:is\s+)?documented\b"),
            "PROTECTED",
            0.92,
        ),
    ]
    for pattern, state, confidence in narrative_patterns:
        for match in pattern.finditer(text):
            _append_unique(
                facts,
                ConfigurationFact(
                    variable=target,
                    state=state,
                    basis="CONTROL_NARRATIVE",
                    source_document_id=str(doc.id),
                    source_title=title,
                    raw_value=None,
                    evidence_text=_compact_excerpt(text, match.start(), match.end()),
                    confidence=confidence,
                ),
            )

    # 4) Operational replay tests are separate facts.  They support later fact
    #    reconciliation but do not silently become a configuration scalar in M01.
    if target == "duplicate_suppression":
        replay_context = any(
            token in lowered
            for token in (
                "duplicate replay",
                "duplicate-replay",
                "repeated event",
                "replay scenario",
                "replay test",
                "replaying",
            )
        )
        if replay_context:
            pass_match = re.search(r"(?is)\b(?:test\s+result|recorded\s+result)\s*[:\-]?\s*pass\b", text)
            fail_match = re.search(r"(?is)\b(?:test\s+result|recorded\s+result)\s*[:\-]?\s*fail\b", text)
            if pass_match:
                _append_unique(
                    facts,
                    ConfigurationFact(
                        variable=target,
                        state="PROTECTED",
                        basis="TEST_ASSERTION",
                        source_document_id=str(doc.id),
                        source_title=title,
                        raw_value="PASS",
                        evidence_text=_compact_excerpt(text, pass_match.start(), pass_match.end()),
                        confidence=0.92,
                    ),
                )
            if fail_match:
                _append_unique(
                    facts,
                    ConfigurationFact(
                        variable=target,
                        state="DISABLED",
                        basis="TEST_ASSERTION",
                        source_document_id=str(doc.id),
                        source_title=title,
                        raw_value="FAIL",
                        evidence_text=_compact_excerpt(text, fail_match.start(), fail_match.end()),
                        confidence=0.92,
                    ),
                )

    return facts


AggregationBasis = Literal[
    "EXPLICIT_SCALAR",
    "CONTROL_NARRATIVE",
    "TEST_ASSERTION",
    "CONFLICT",
    "NO_EVIDENCE",
]


class ConfigurationFactAssessment(BaseModel):
    """Candidate-level reconciliation of source-grounded configuration facts.

    R94.0.6-M02 combines M01 facts without turning lower-quality operational
    signals into invented scalar configuration values. Exact scalar evidence has
    precedence for the requested variable. When no scalar exists, consistent
    configuration narratives can establish a control state, with test assertions
    used as corroboration. Material contradictions remain UNKNOWN and fail closed.
    """

    variable: str
    state: FactState
    resolution_basis: AggregationBasis
    confidence: float = Field(ge=0.0, le=1.0)
    supporting_document_ids: list[str] = Field(default_factory=list)
    conflicting_document_ids: list[str] = Field(default_factory=list)
    facts: list[ConfigurationFact] = Field(default_factory=list)
    conflict_reason: str | None = None
    warnings: list[str] = Field(default_factory=list)


def _unique_document_ids(facts: list[ConfigurationFact]) -> list[str]:
    return list(dict.fromkeys(str(f.source_document_id) for f in facts))


def _positive(state: FactState) -> bool:
    return state in {"ENABLED", "PROTECTED"}


def _opposes(left: FactState, right: FactState) -> bool:
    if left == "UNKNOWN" or right == "UNKNOWN":
        return False
    return _positive(left) != _positive(right)


def aggregate_configuration_facts(
    facts: list[ConfigurationFact],
    variable: str,
) -> ConfigurationFactAssessment:
    """Reconcile M01 facts for one candidate and one configuration variable.

    Precedence is deliberately glass-box:
    1. Conflicting explicit scalar values => UNKNOWN / fail closed.
    2. One consistent explicit scalar value is the authoritative current scalar.
       Lower-tier contradictory behavior is surfaced as a warning, not allowed to
       rewrite the persisted scalar.
    3. Without a scalar, conflicting configuration narratives => UNKNOWN.
    4. A consistent configuration narrative may establish DISABLED/PROTECTED.
       A contradictory test assertion makes the result UNKNOWN because there is no
       exact scalar capable of resolving configuration-vs-runtime divergence.
    5. Test-only facts may establish an operational state if consistent.
    6. No facts => UNKNOWN / NO_EVIDENCE.
    """

    target = normalize_configuration_key(variable)
    relevant = [f for f in facts if normalize_configuration_key(f.variable) == target]
    if not relevant:
        return ConfigurationFactAssessment(
            variable=target,
            state="UNKNOWN",
            resolution_basis="NO_EVIDENCE",
            confidence=0.0,
            facts=[],
            conflict_reason="NO_CONFIGURATION_FACTS",
        )

    explicit = [f for f in relevant if f.basis == "EXPLICIT_SCALAR"]
    narrative = [f for f in relevant if f.basis == "CONTROL_NARRATIVE"]
    tests = [f for f in relevant if f.basis == "TEST_ASSERTION"]

    # Exact scalar values are the highest-quality evidence for a scalar change.
    if explicit:
        scalar_states = list(dict.fromkeys(f.state for f in explicit))
        if len(scalar_states) > 1:
            return ConfigurationFactAssessment(
                variable=target,
                state="UNKNOWN",
                resolution_basis="CONFLICT",
                confidence=0.0,
                supporting_document_ids=[],
                conflicting_document_ids=_unique_document_ids(explicit),
                facts=relevant,
                conflict_reason="CONFLICTING_EXPLICIT_SCALARS",
            )

        selected = scalar_states[0]
        selected_facts = [f for f in explicit if f.state == selected]
        lower_tier_opposition = [f for f in narrative + tests if _opposes(selected, f.state)]
        warnings: list[str] = []
        if lower_tier_opposition:
            warnings.append("LOWER_TIER_SIGNAL_DIVERGENCE")
        return ConfigurationFactAssessment(
            variable=target,
            state=selected,
            resolution_basis="EXPLICIT_SCALAR",
            confidence=max(f.confidence for f in selected_facts),
            supporting_document_ids=_unique_document_ids(selected_facts),
            conflicting_document_ids=_unique_document_ids(lower_tier_opposition),
            facts=relevant,
            warnings=warnings,
        )

    # Without an exact scalar, configuration narratives are next in precedence.
    if narrative:
        narrative_polarities = {"POSITIVE" if _positive(f.state) else "NEGATIVE" for f in narrative}
        if len(narrative_polarities) > 1:
            return ConfigurationFactAssessment(
                variable=target,
                state="UNKNOWN",
                resolution_basis="CONFLICT",
                confidence=0.0,
                conflicting_document_ids=_unique_document_ids(narrative),
                facts=relevant,
                conflict_reason="CONFLICTING_CONTROL_NARRATIVES",
            )

        # Preserve PROTECTED when the source only documents protection; do not
        # silently rewrite it to literal ENABLED.
        selected = "PROTECTED" if any(f.state == "PROTECTED" for f in narrative) else narrative[0].state
        opposing_tests = [f for f in tests if _opposes(selected, f.state)]
        if opposing_tests:
            return ConfigurationFactAssessment(
                variable=target,
                state="UNKNOWN",
                resolution_basis="CONFLICT",
                confidence=0.0,
                supporting_document_ids=_unique_document_ids(narrative),
                conflicting_document_ids=_unique_document_ids(opposing_tests),
                facts=relevant,
                conflict_reason="CONFIGURATION_EXECUTION_DIVERGENCE",
            )
        supporting = narrative + [f for f in tests if not _opposes(selected, f.state)]
        return ConfigurationFactAssessment(
            variable=target,
            state=selected,
            resolution_basis="CONTROL_NARRATIVE",
            confidence=max(f.confidence for f in narrative),
            supporting_document_ids=_unique_document_ids(supporting),
            facts=relevant,
        )

    # Test-only evidence describes the operational state, not a literal persisted
    # scalar, but it is still useful when no configuration fact exists.
    test_polarities = {"POSITIVE" if _positive(f.state) else "NEGATIVE" for f in tests}
    if len(test_polarities) > 1:
        return ConfigurationFactAssessment(
            variable=target,
            state="UNKNOWN",
            resolution_basis="CONFLICT",
            confidence=0.0,
            conflicting_document_ids=_unique_document_ids(tests),
            facts=relevant,
            conflict_reason="CONFLICTING_TEST_ASSERTIONS",
        )
    selected = "PROTECTED" if any(f.state == "PROTECTED" for f in tests) else tests[0].state
    return ConfigurationFactAssessment(
        variable=target,
        state=selected,
        resolution_basis="TEST_ASSERTION",
        confidence=max(f.confidence for f in tests),
        supporting_document_ids=_unique_document_ids(tests),
        facts=relevant,
        warnings=["TEST_ONLY_STATE"],
    )


def assess_configuration_documents(
    docs: list[EvidenceDocument],
    variable: str,
) -> ConfigurationFactAssessment:
    """Extract and aggregate one variable across candidate-specific documents."""

    facts: list[ConfigurationFact] = []
    for doc in docs:
        facts.extend(extract_configuration_facts(doc, variable))
    return aggregate_configuration_facts(facts, variable)
