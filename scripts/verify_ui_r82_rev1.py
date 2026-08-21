from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
api = (ROOT / "frontend/lib/api.ts").read_text(encoding="utf-8")
sidebar = (ROOT / "frontend/components/sidebar.tsx").read_text(encoding="utf-8")
page = (ROOT / "frontend/app/methods/page.tsx").read_text(encoding="utf-8")
workspace = (ROOT / "frontend/components/method-registry-workspace.tsx").read_text(encoding="utf-8")
css = (ROOT / "frontend/app/globals.css").read_text(encoding="utf-8")
domain_api = (ROOT / "backend/app/api/domain.py").read_text(encoding="utf-8")
domain_service = (ROOT / "backend/app/services/domain.py").read_text(encoding="utf-8")
repo = (ROOT / "backend/app/repositories/domain.py").read_text(encoding="utf-8")

checks = {
    "methods route": 'active="Methods"' in page and "MethodRegistryWorkspace" in page,
    "methods nav": '{ label: "Methods", icon: GitBranch, href: "/methods" }' in sidebar,
    "real method list/create": '/api/v1/domain/methods' in api and 'export async function createDeliveryMethod' in api,
    "real version list/create": '/api/v1/domain/method-versions' in api and 'export async function createDraftMethodVersion' in api,
    "backend method endpoints": '@router.get("/methods"' in domain_api and '@router.post("/methods"' in domain_api,
    "backend version endpoints": '@router.get("/method-versions"' in domain_api and '@router.post("/method-versions"' in domain_api,
    "module prerequisite": 'MODULE_NOT_FOUND' in domain_api,
    "method prerequisite": 'METHOD_NOT_FOUND' in domain_api,
    "draft forced backend": 'status=MethodVersionStatus.DRAFT.value' in domain_service,
    "no status input": 'class MethodVersionCreate(BaseModel):\n    method_id:' in domain_api and 'status: str = Field' not in domain_api and 'name="status"' not in workspace,
    "method idempotency": 'get_delivery_method(module_id=module.id, name=name)' in domain_service,
    "version idempotency": 'get_method_version(method_id=method.id, version=version)' in domain_service,
    "repository persistence helpers": 'def list_delivery_methods' in repo and 'def list_method_versions' in repo,
    "audit provenance": 'action="DELIVERY_METHOD_CREATED"' in domain_service and 'action="METHOD_VERSION_DRAFT_CREATED"' in domain_service,
    "no abom mutation": 'create_edge' not in domain_api and 'USES_METHOD_VERSION' not in workspace,
    "governance boundary copy": 'Approval and A-BOM adoption happen elsewhere' in workspace,
    "semantic method states": 'APPROVED' in workspace and 'PROPOSED' in workspace and 'REVOKED' in workspace and 'DRAFT' in workspace,
    "lucide icons": 'from "lucide-react"' in workspace and 'GitBranch' in sidebar,
    "scoped styles": '.method-registry-r82' in css and '.method-version-create-r82' in css,
    "responsive hardening": '@media (max-width:560px)' in css and '.method-row-r82 { grid-template-columns:1fr; }' in css,
}

failures = [name for name, passed in checks.items() if not passed]
for name, passed in checks.items():
    print(f"{'PASS' if passed else 'FAIL'}  {name}")
if failures:
    raise SystemExit("UI-R82 REV1 verification failed: " + ", ".join(failures))
print("UI-R82 REV1 verifier PASS")
