from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
api = (ROOT / "frontend/lib/api.ts").read_text(encoding="utf-8")
sidebar = (ROOT / "frontend/components/sidebar.tsx").read_text(encoding="utf-8")
page = (ROOT / "frontend/app/dependencies/page.tsx").read_text(encoding="utf-8")
workspace = (ROOT / "frontend/components/dependency-registry-workspace.tsx").read_text(encoding="utf-8")
css = (ROOT / "frontend/app/globals.css").read_text(encoding="utf-8")
domain_api = (ROOT / "backend/app/api/domain.py").read_text(encoding="utf-8")
domain_service = (ROOT / "backend/app/services/domain.py").read_text(encoding="utf-8")
repo = (ROOT / "backend/app/repositories/domain.py").read_text(encoding="utf-8")

checks = {
    "dependencies route": 'active="Dependencies"' in page and "DependencyRegistryWorkspace" in page,
    "dependencies nav": '{ label: "Dependencies", icon: Network, href: "/dependencies" }' in sidebar,
    "real dependency list/create/remove": '/api/v1/domain/dependencies' in api and 'createImplementationMethodDependency' in api and 'removeImplementationMethodDependency' in api,
    "backend dependency endpoints": '@router.get("/dependencies"' in domain_api and '@router.post("/dependencies"' in domain_api and '@router.delete("/dependencies/{dependency_id}"' in domain_api,
    "explicit relationship only": 'relationship="USES_METHOD_VERSION"' in domain_service and 'source_type="Implementation"' in domain_service and 'target_type="MethodVersion"' in domain_service,
    "evidence required by create schema": 'evidence_document_id: str = Field(min_length=1, max_length=36)' in domain_api,
    "module compatibility enforced": 'IMPLEMENTATION_METHOD_MODULE_MISMATCH' in domain_api and 'method_version.method.module_id != implementation.module_id' in domain_service,
    "no evidence replacement": 'DEPENDENCY_ALREADY_EXISTS_WITH_DIFFERENT_EVIDENCE' in domain_service,
    "audited registration/removal": 'action="ABOM_DEPENDENCY_REGISTERED"' in domain_service and 'action="ABOM_DEPENDENCY_REMOVED"' in domain_service,
    "repository helpers": 'def list_implementation_method_dependencies' in repo and 'def get_implementation_method_dependency' in repo,
    "human boundary copy": 'does not approve the method' in workspace and 'Impact, Human Decision, adoption and recall remain separate governed workflows' in workspace,
    "evidence boundary UI": 'Supporting evidence' in workspace and 'documents.length > 0' in workspace,
    "destructive correction requires reason": 'removeReason.trim()' in workspace and 'Reason <b>Required</b>' in workspace,
    "lucide icons": 'from "lucide-react"' in workspace and 'Network' in sidebar,
    "scoped styles": '.dependency-registry-r83' in css and '.dependency-remove-r83' in css,
    "responsive hardening": '@media (max-width:560px)' in css and '.dependency-row-r83 { grid-template-columns:1fr; }' in css,
    "no generic edge authoring UI": 'relationship' not in ''.join(line for line in workspace.splitlines() if '<select' in line or '<option' in line),
}

failures = [name for name, passed in checks.items() if not passed]
for name, passed in checks.items():
    print(f"{'PASS' if passed else 'FAIL'}  {name}")
if failures:
    raise SystemExit("UI-R83 REV1 verification failed: " + ", ".join(failures))
print("UI-R83 REV1 verifier PASS")
