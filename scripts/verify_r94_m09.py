from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ENFORCEMENT = ROOT / "backend" / "app" / "services" / "adoption_enforcement.py"
DOMAIN_SERVICE = ROOT / "backend" / "app" / "services" / "domain.py"
ADVANCED = ROOT / "backend" / "app" / "services" / "advanced.py"
DOMAIN_API = ROOT / "backend" / "app" / "api" / "domain.py"
FRONT_API = ROOT / "frontend" / "lib" / "api.ts"
DEPENDENCIES = ROOT / "frontend" / "components" / "dependency-registry-workspace.tsx"
TEST = ROOT / "backend" / "tests" / "test_r94_m09_scope_aware_adoption_enforcement.py"


def require(text: str, needle: str) -> None:
    if needle not in text:
        raise SystemExit(f"FAIL: missing R94-M09 contract: {needle}")


def main() -> None:
    enforcement = ENFORCEMENT.read_text(encoding="utf-8")
    domain_service = DOMAIN_SERVICE.read_text(encoding="utf-8")
    advanced = ADVANCED.read_text(encoding="utf-8")
    domain_api = DOMAIN_API.read_text(encoding="utf-8")
    front_api = FRONT_API.read_text(encoding="utf-8")
    dependencies = DEPENDENCIES.read_text(encoding="utf-8")
    test = TEST.read_text(encoding="utf-8")

    for needle in (
        'SUPPORTED_SCOPE_MODES = {',
        'def adoption_policy_for_version(',
        'def adoption_eligibility(',
        'ADOPTION_RECEIPT_INTEGRITY_INVALID',
        'ADOPTION_SCOPE_EXCLUDES_IMPLEMENTATION',
        'METHOD_CATALOG_SCOPE',
        'IMPLEMENTATION_WITHIN_SIGNED_SCOPE',
    ):
        require(enforcement, needle)

    for needle in (
        'from app.services.adoption_enforcement import adoption_eligibility',
        'adoption = adoption_eligibility(',
        '"adoption_scope_enforced": bool(adoption["enforced"])',
        '"adoption_receipt_id": adoption.get("receipt_id")',
    ):
        require(domain_service, needle)

    for needle in (
        'adoption_policy_for_version(db, version.id)',
        'eligibility=adoption_eligibility(db,method_version=version,implementation=impl)',
        '"blocked_candidate_count": len(blocked_scope)',
        '"blocked_candidates": blocked_scope',
    ):
        require(advanced, needle)

    for needle in (
        'adoption_policy: dict | None = None',
        'adoption_policy=adoption_policy_for_version(db, item.id)',
    ):
        require(domain_api, needle)

    for needle in (
        'adoption_policy?: {',
        'scope_mode: "METHOD_CATALOG" | "CURRENT_REGISTERED_IMPLEMENTATIONS" | "SELECTED_IMPLEMENTATIONS" | null;',
        'receipt_integrity: "VALID" | "INVALID" | null;',
    ):
        require(front_api, needle)

    for needle in (
        'function adoptionEligibility(',
        'Outside signed scope',
        'Governed learned versions are additionally constrained by their Signed Adoption Receipt.',
        'ADOPTION_RECEIPT_INTEGRITY_INVALID',
        'ADOPTION_SCOPE_EXCLUDES_IMPLEMENTATION',
    ):
        require(dependencies, needle)

    for needle in (
        'test_selected_scope_allows_only_signed_implementations',
        'test_current_registered_scope_is_frozen_at_approval_time',
        'test_method_catalog_scope_allows_future_same_module_implementation',
        'test_receipt_tampering_blocks_future_reuse',
        'test_blast_radius_filters_preexisting_out_of_scope_edges',
    ):
        require(test, needle)

    print("R94-M09 source contract: PASS")


if __name__ == "__main__":
    main()
