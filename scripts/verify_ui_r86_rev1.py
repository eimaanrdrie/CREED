from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

sidebar = (ROOT / "frontend/components/sidebar.tsx").read_text(encoding="utf-8")
page = (ROOT / "frontend/app/deployments/page.tsx").read_text(encoding="utf-8")
workspace = (ROOT / "frontend/components/deployment-registry-workspace.tsx").read_text(encoding="utf-8")
api = (ROOT / "frontend/lib/api.ts").read_text(encoding="utf-8")
css = (ROOT / "frontend/app/globals.css").read_text(encoding="utf-8")
models = (ROOT / "backend/app/domain/models.py").read_text(encoding="utf-8")
domain_api = (ROOT / "backend/app/api/domain.py").read_text(encoding="utf-8")
service = (ROOT / "backend/app/services/domain.py").read_text(encoding="utf-8")
repo = (ROOT / "backend/app/repositories/domain.py").read_text(encoding="utf-8")
migration = (ROOT / "backend/migrations/versions/e1f2a3b4c5d6_r86_release_deployment_registry.py").read_text(encoding="utf-8")

checks = {
    "deployments route exists": 'active="Deployments"' in page and "DeploymentRegistryWorkspace" in page,
    "sidebar navigation": '{ label: "Deployments", icon: Rocket, href: "/deployments" }' in sidebar,
    "lucide deployment icon": 'Rocket' in sidebar and 'from "lucide-react"' in workspace,
    "real deployment list api": 'GET' not in api or 'getDeployments' in api,
    "frontend create api": 'createDeployment' in api and '/api/v1/domain/deployments' in api,
    "backend deployment model": 'class ImplementationDeployment' in models and '__tablename__ = "implementation_deployments"' in models,
    "evidence provenance field": 'evidence_document_id' in models and 'evidence_document_id: str = Field' in domain_api,
    "environment validation": 'DEVELOPMENT' in domain_api and 'PRODUCTION' in domain_api and 'DR' in domain_api,
    "release inherited": 'release_version=implementation.release_version' in domain_api and 'Change the release in the Implementation Registry, not here.' in workspace,
    "deployment endpoints": '@router.get("/deployments"' in domain_api and '@router.post("/deployments"' in domain_api,
    "idempotent conflict boundary": 'DEPLOYMENT_EVENT_ALREADY_EXISTS' in service and 'DEPLOYMENT_EVENT_ALREADY_EXISTS' in domain_api,
    "audit provenance": 'RELEASE_DEPLOYMENT_RECORDED' in service,
    "repository list": 'def list_deployments' in repo and 'def get_deployment_event' in repo,
    "migration chain": 'down_revision: Union[str, None] = "d0e1f2a3b4c5"' in migration,
    "r86 responsive css": '.deployment-registry-r86' in css and '@media (max-width:560px)' in css,
    "no fake method adoption": 'createImplementationMethodDependency' not in workspace and 'USES_METHOD_VERSION' not in workspace,
}

failed = [name for name, ok in checks.items() if not ok]
for name, ok in checks.items():
    print(f"{'PASS' if ok else 'FAIL'}  {name}")
if failed:
    raise SystemExit("UI-R86 REV1 verifier failed: " + ", ".join(failed))
print("UI-R86 REV1 verifier PASS")
