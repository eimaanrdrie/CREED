from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ADVANCED = ROOT / "backend" / "app" / "services" / "advanced.py"
API = ROOT / "backend" / "app" / "api" / "advanced.py"
FRONT_API = ROOT / "frontend" / "lib" / "api.ts"
SHELL = ROOT / "frontend" / "components" / "analysis-shell.tsx"
CSS = ROOT / "frontend" / "app" / "globals.css"
TEST = ROOT / "backend" / "tests" / "test_r94_m08_adoption_scope_receipt.py"


def require(text: str, needle: str) -> None:
    if needle not in text:
        raise SystemExit(f"FAIL: missing R94-M08 contract: {needle}")


def main() -> None:
    advanced = ADVANCED.read_text(encoding="utf-8")
    api = API.read_text(encoding="utf-8")
    front_api = FRONT_API.read_text(encoding="utf-8")
    shell = SHELL.read_text(encoding="utf-8")
    css = CSS.read_text(encoding="utf-8")
    test = TEST.read_text(encoding="utf-8")

    for needle in (
        'ADOPTION_SCOPE_MODES={"METHOD_CATALOG","CURRENT_REGISTERED_IMPLEMENTATIONS","SELECTED_IMPLEMENTATIONS"}',
        'def canonical_adoption_scope(',
        'raise ValueError("ADOPTION_SCOPE_REQUIRED")',
        'raise ValueError("ADOPTION_SCOPE_IMPLEMENTATION_NOT_REGISTERED")',
        '"automatic_deployment_change":False',
        '"adoption_scope":canonical_scope',
        'receipt_version="1.1"',
    ):
        require(advanced, needle)

    for needle in (
        'class AdoptionScopeInput(BaseModel):',
        "'METHOD_CATALOG','CURRENT_REGISTERED_IMPLEMENTATIONS','SELECTED_IMPLEMENTATIONS'",
        'adoption_scope:AdoptionScopeInput|None=None',
        'payload.adoption_scope.model_dump() if payload.adoption_scope else None',
    ):
        require(api, needle)

    for needle in (
        'export type AdoptionScopeMode',
        'export type AdoptionScopeSummary',
        'export type AdoptionScopeInput',
        'export type MethodAbom',
        'getMethodAbom',
    ):
        require(front_api, needle)

    for needle in (
        'ADOPTION SCOPE',
        'Method catalog',
        'Current registered adopters',
        'Selected implementations',
        'implementation_ids:scopeMode === "SELECTED_IMPLEMENTATIONS" ? selectedScopeIds : []',
        'formatAdoptionScope',
        'Implementations sealed into scope',
    ):
        require(shell, needle)

    require(css, 'R94-M08 — Human Adoption Scope & Receipt Binding')
    for needle in (
        'test_current_registered_scope_is_canonicalized_and_signed',
        'test_selected_scope_accepts_only_registered_abom_adopters',
        'test_selected_scope_rejects_non_registered_implementation_and_does_not_adopt',
        'test_approval_requires_explicit_scope_but_rejection_does_not',
    ):
        require(test, needle)
    print("R94-M08 source contract: PASS")


if __name__ == "__main__":
    main()
