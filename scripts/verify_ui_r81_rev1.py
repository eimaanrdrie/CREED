from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
api = (ROOT / "frontend/lib/api.ts").read_text(encoding="utf-8")
sidebar = (ROOT / "frontend/components/sidebar.tsx").read_text(encoding="utf-8")
page = (ROOT / "frontend/app/implementations/page.tsx").read_text(encoding="utf-8")
workspace = (ROOT / "frontend/components/implementation-registry-workspace.tsx").read_text(encoding="utf-8")
css = (ROOT / "frontend/app/globals.css").read_text(encoding="utf-8")
domain_api = (ROOT / "backend/app/api/domain.py").read_text(encoding="utf-8")
domain_service = (ROOT / "backend/app/services/domain.py").read_text(encoding="utf-8")

checks = {
    "implementations route": 'active="Implementations"' in page and "ImplementationRegistryWorkspace" in page,
    "implementation nav": '{ label: "Implementations", icon: Boxes, href: "/implementations" }' in sidebar,
    "real implementation list": 'fetch(`${API_BASE_URL}/api/v1/domain/implementations`' in api,
    "real implementation create": 'export async function createImplementation' in api and 'method: "POST"' in api,
    "real catalog reads": '/api/v1/domain/products' in api and '/api/v1/domain/modules' in api,
    "backend implementation endpoints": '@router.get("/implementations"' in domain_api and '@router.post("/implementations"' in domain_api,
    "backend product module validation": 'MODULE_PRODUCT_MISMATCH' in domain_api,
    "backend persisted audit": 'action="IMPLEMENTATION_CREATED"' in domain_service,
    "backend idempotent release": 'get_implementation_release' in domain_service,
    "product constrained modules": 'modules.filter(module => module.product_id === productId)' in workspace,
    "load and catalog failures surfaced": 'Implementation registry unavailable' in workspace and 'Implementation catalog unavailable' in workspace,
    "client prerequisite surfaced": 'A client is required first' in workspace and 'href="/clients"' in workspace,
    "separate from A-BOM mutation": 'create_edge' not in domain_api and 'DependencyEdge' not in workspace,
    "no method version creation": 'MethodVersion' not in workspace and 'method_version_id' not in workspace,
    "lucide icons": 'from "lucide-react"' in workspace,
    "scoped styles": '.implementation-registry-r81' in css and '.implementation-row-r81' in css,
}

failures = [name for name, passed in checks.items() if not passed]
for name, passed in checks.items():
    print(f"{'PASS' if passed else 'FAIL'}  {name}")
if failures:
    raise SystemExit("UI-R81 REV1 verification failed: " + ", ".join(failures))
print("UI-R81 REV1 verifier PASS")
