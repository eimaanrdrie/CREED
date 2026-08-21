from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ADVANCED = ROOT / "backend" / "app" / "services" / "advanced.py"
ADVANCED_API = ROOT / "backend" / "app" / "api" / "advanced.py"
FRONT_API = ROOT / "frontend" / "lib" / "api.ts"
RECALLS = ROOT / "frontend" / "components" / "recalls-workspace.tsx"
NOTICE = ROOT / "frontend" / "components" / "recall-notice-workspace.tsx"
TEST = ROOT / "backend" / "tests" / "test_r94_m10_scope_aware_recall_propagation.py"
NOTES = ROOT / "R94_M10_NOTES.md"


def require(text: str, needle: str) -> None:
    if needle not in text:
        raise SystemExit(f"FAIL: missing R94-M10 contract: {needle}")


def main() -> None:
    advanced = ADVANCED.read_text(encoding="utf-8")
    advanced_api = ADVANCED_API.read_text(encoding="utf-8")
    front_api = FRONT_API.read_text(encoding="utf-8")
    recalls = RECALLS.read_text(encoding="utf-8")
    notice = NOTICE.read_text(encoding="utf-8")
    test = TEST.read_text(encoding="utf-8")
    notes = NOTES.read_text(encoding="utf-8")

    for needle in (
        'adoption_policy=adoption_policy_for_version(db,v.id)',
        'if adoption_policy is not None and adoption_policy.get("reason")!="READY"',
        'eligibility=adoption_eligibility(db,method_version=v,implementation=impl)',
        '"basis": "SIGNED_ADOPTION_SCOPE_INTERSECT_CURRENT_A_BOM"',
        '"blocked_implementations": blocked',
        'notice_version="1.1"',
        'scope-aware recall routing',
        '"routing_scope":routing_scope',
    ):
        require(advanced, needle)

    for needle in (
        "'adoption_policy':adoption_policy_for_version(db,v.id)",
        "@router.get('/knowledge-graph/method-versions')",
    ):
        require(advanced_api, needle)

    for needle in (
        'routing_scope: {',
        'explicit_dependency_count: number;',
        'blocked_implementations: Array<{ implementation_id: string; dependency_edge_id: string; reason: string }>;',
        'adoption_policy?: {',
    ):
        require(front_api, needle)

    for needle in (
        'const selectedPolicyReady =',
        'Signed adoption boundary',
        'Out-of-scope legacy edges are recorded but do not become review obligations.',
        'Recall scope',
        'Excluded edges',
    ):
        require(recalls, needle)

    for needle in (
        'Recall scope proof',
        'SIGNED SCOPE',
        'notice.routing_scope.blocked_implementations',
        'current Local A-BOM use intersects the signed adoption scope',
    ):
        require(notice, needle)

    for needle in (
        'test_selected_scope_routes_only_intersection_and_creates_run_scoped_review_obligations',
        'test_tampered_adoption_receipt_blocks_recall_before_revocation_mutation',
        'test_method_catalog_scope_routes_future_explicit_same_module_adopter',
        'test_baseline_recall_preserves_explicit_abom_behavior_without_learning_scope',
    ):
        require(test, needle)

    require(notes, 'R94-M10 REV1')
    print("R94-M10 source contract: PASS")


if __name__ == "__main__":
    main()
