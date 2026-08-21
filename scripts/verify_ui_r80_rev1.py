from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
api = (ROOT / "frontend/lib/api.ts").read_text(encoding="utf-8")
sidebar = (ROOT / "frontend/components/sidebar.tsx").read_text(encoding="utf-8")
page = (ROOT / "frontend/app/clients/page.tsx").read_text(encoding="utf-8")
workspace = (ROOT / "frontend/components/client-registry-workspace.tsx").read_text(encoding="utf-8")
css = (ROOT / "frontend/app/globals.css").read_text(encoding="utf-8")
domain_api = (ROOT / "backend/app/api/domain.py").read_text(encoding="utf-8")

checks = {
    "clients route": 'active="Clients"' in page and "ClientRegistryWorkspace" in page,
    "client nav": '{ label: "Clients", icon: Building2, href: "/clients" }' in sidebar,
    "real list endpoint": 'fetch(`${API_BASE_URL}/api/v1/domain/clients`' in api,
    "real create method": 'export async function createClient' in api and 'method: "POST"' in api,
    "existing backend endpoint retained": '@router.post("/clients"' in domain_api,
    "backend idempotency not duplicated in UI": "already exists in the client registry" in workspace,
    "load failure surfaced": "Client registry unavailable" in workspace and "disabled={loadError}" in workspace,
    "no implementation registry in module": "/implementations" not in page and "ImplementationRegistry" not in workspace,
    "no inferred implementation count": "implementation_count" not in workspace and "implementations.length" not in workspace,
    "lucide icons": 'from "lucide-react"' in workspace,
    "scoped styles": ".client-registry-r80" in css and ".client-row-r80" in css,
}

failures = [name for name, passed in checks.items() if not passed]
for name, passed in checks.items():
    print(f"{'PASS' if passed else 'FAIL'}  {name}")
if failures:
    raise SystemExit("UI-R80 REV1 verification failed: " + ", ".join(failures))
print("UI-R80 REV1 verifier PASS")
