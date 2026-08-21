from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ADVANCED = ROOT / "backend" / "app" / "services" / "advanced.py"
TEST = ROOT / "backend" / "tests" / "test_r94_m01_abom_evidence_routing.py"


def require(text: str, needle: str) -> None:
    if needle not in text:
        raise SystemExit(f"FAIL: missing contract: {needle}")


def main() -> None:
    source = ADVANCED.read_text(encoding="utf-8")
    test = TEST.read_text(encoding="utf-8")

    for needle in (
        'DependencyEdge.evidence_document_id.in_(doc_ids)',
        'DependencyEdge.relationship=="USES_METHOD_VERSION"',
        'def _implementation_supporting_document_ids(',
        'cfg_doc_ids.add(str(evidence_id))',
        '_candidate_impl_document_ids',
    ):
        require(source, needle)

    for needle in (
        'test_r93_ui_abom_supporting_evidence_resolves_method_version',
        'test_r93_ui_abom_supporting_evidence_is_candidate_specific_evidence',
        'test_r93_ui_abom_shape_routes_all_registered_adopters',
        'assert len(impact["results"]) == 3',
    ):
        require(test, needle)

    print("R94-M01 source contract: PASS")


if __name__ == "__main__":
    main()
