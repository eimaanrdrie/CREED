from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
page = (ROOT / "frontend/app/modules/page.tsx").read_text(encoding="utf-8")
workspace = (ROOT / "frontend/components/module-registry-workspace.tsx").read_text(encoding="utf-8")
sidebar = (ROOT / "frontend/components/sidebar.tsx").read_text(encoding="utf-8")
api = (ROOT / "frontend/lib/api.ts").read_text(encoding="utf-8")
css = (ROOT / "frontend/app/globals.css").read_text(encoding="utf-8")
models = (ROOT / "backend/app/domain/models.py").read_text(encoding="utf-8")
domain_api = (ROOT / "backend/app/api/domain.py").read_text(encoding="utf-8")
service = (ROOT / "backend/app/services/domain.py").read_text(encoding="utf-8")
repo = (ROOT / "backend/app/repositories/domain.py").read_text(encoding="utf-8")
migration = (ROOT / "backend/migrations/versions/h4c5d6e7f8g9_r90_module_registry.py").read_text(encoding="utf-8")
design = (ROOT / "frontend/DESIGN.md").read_text(encoding="utf-8")

checks = {
    "modules route exists": 'active="Modules"' in page and "ModuleRegistryWorkspace" in page and "getModules" in page and "getProducts" in page,
    "registry navigation": '{ label: "Modules", icon: FolderTree, href: "/modules" }' in sidebar,
    "registry description": 'Modules: "Product capability catalog"' in sidebar,
    "lucide only": 'from "lucide-react"' in workspace and "FolderTree" in workspace,
    "real module API client": all(token in api for token in ["createModule", "updateModule", "/api/v1/domain/modules", "ModuleCreatePayload", "ModuleUpdatePayload"]),
    "module active type": "active: boolean;" in api and "class Module" in models and "active: Mapped[bool]" in models,
    "backend create endpoint": '@router.post("/modules"' in domain_api and "ModuleCreate" in domain_api,
    "backend update endpoint": '@router.patch("/modules/{module_id}"' in domain_api and "ModuleUpdate" in domain_api,
    "active product guard": "PRODUCT_INACTIVE" in domain_api and "activeProducts" in workspace,
    "duplicate conflict": "MODULE_NAME_ALREADY_EXISTS" in service and "MODULE_NAME_ALREADY_EXISTS" in domain_api,
    "audit lifecycle": "MODULE_CREATED" in service and "MODULE_UPDATED" in service,
    "sorted repository": "def list_modules" in repo and "order_by(Module.name)" in repo,
    "migration chain": 'down_revision: Union[str, None] = "g3b4c5d6e7f8"' in migration,
    "migration active column": 'op.add_column("modules"' in migration and '"active"' in migration and "ix_modules_active" in migration,
    "method boundary": "Methods and implementations remain separate" in workspace and "createDeliveryMethod" not in workspace,
    "operate create surface": "module-create-r90" in workspace and "showCreate" in workspace,
    "product and status filters": "productFilter" in workspace and "statusFilter" in workspace and "module-search-r90" in workspace,
    "explicit prerequisite and empty states": "Active product required" in workspace and "No products registered" in workspace and "No modules registered" in workspace,
    "responsive css": ".module-registry-r90" in css and "@media (max-width:560px)" in css,
    "no modal first": 'role="dialog"' not in workspace,
    "design contract": "UI-R90 REV1 — Module Registry" in design and "Module creation never creates a Method" in design,
}

failed = [name for name, ok in checks.items() if not ok]
for name, ok in checks.items():
    print(f"{'PASS' if ok else 'FAIL'}  {name}")
if failed:
    raise SystemExit("UI-R90 REV1 verifier failed: " + ", ".join(failed))
print("UI-R90 REV1 verifier PASS")
