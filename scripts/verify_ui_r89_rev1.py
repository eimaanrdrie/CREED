from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
page = (ROOT / "frontend/app/products/page.tsx").read_text(encoding="utf-8")
workspace = (ROOT / "frontend/components/product-registry-workspace.tsx").read_text(encoding="utf-8")
sidebar = (ROOT / "frontend/components/sidebar.tsx").read_text(encoding="utf-8")
api = (ROOT / "frontend/lib/api.ts").read_text(encoding="utf-8")
css = (ROOT / "frontend/app/globals.css").read_text(encoding="utf-8")
models = (ROOT / "backend/app/domain/models.py").read_text(encoding="utf-8")
domain_api = (ROOT / "backend/app/api/domain.py").read_text(encoding="utf-8")
service = (ROOT / "backend/app/services/domain.py").read_text(encoding="utf-8")
repo = (ROOT / "backend/app/repositories/domain.py").read_text(encoding="utf-8")
migration = (ROOT / "backend/migrations/versions/g3b4c5d6e7f8_r89_product_registry.py").read_text(encoding="utf-8")
design = (ROOT / "frontend/DESIGN.md").read_text(encoding="utf-8")

checks = {
    "products route exists": 'active="Products"' in page and "ProductRegistryWorkspace" in page and "getProducts" in page,
    "registry navigation": '{ label: "Products", icon: Package, href: "/products" }' in sidebar,
    "registry description": 'Products: "Delivery product catalog"' in sidebar,
    "lucide only": 'from "lucide-react"' in workspace and "Package" in workspace,
    "real product API client": all(token in api for token in [
        "createProduct", "updateProduct", "/api/v1/domain/products", "ProductCreatePayload", "ProductUpdatePayload"
    ]),
    "product active type": "active: boolean;" in api and "active: Mapped[bool]" in models,
    "backend create endpoint": '@router.post("/products"' in domain_api and "ProductCreate" in domain_api,
    "backend update endpoint": '@router.patch("/products/{product_id}"' in domain_api and "ProductUpdate" in domain_api,
    "duplicate conflict": "PRODUCT_NAME_ALREADY_EXISTS" in service and "PRODUCT_NAME_ALREADY_EXISTS" in domain_api,
    "audit lifecycle": "PRODUCT_CREATED" in service and "PRODUCT_UPDATED" in service,
    "sorted repository": "def list_products" in repo and "order_by(Product.name)" in repo,
    "migration chain": 'down_revision: Union[str, None] = "f2a3b4c5d6e7"' in migration,
    "migration active column": 'op.add_column("products"' in migration and '"active"' in migration and "ix_products_active" in migration,
    "module boundary": "Modules are registered separately" in workspace and "createModule" not in workspace,
    "operate create surface": "product-create-r89" in workspace and "showCreate" in workspace,
    "search and status filter": "product-search-r89" in workspace and "statusFilter" in workspace,
    "explicit empty error states": "No products registered" in workspace and "Product catalog unavailable" in workspace,
    "responsive css": ".product-registry-r89" in css and "@media (max-width:560px)" in css,
    "registry flyout remains viewport clamped": "max-height:calc(100vh - 24px)" in css and "transform:translateY(-50%)" in css,
    "no modal first": 'role="dialog"' not in workspace,
    "design contract": "UI-R89 REV1 — Product Registry" in design and "product creation never creates a Module" in design,
}

failed = [name for name, ok in checks.items() if not ok]
for name, ok in checks.items():
    print(f"{'PASS' if ok else 'FAIL'}  {name}")
if failed:
    raise SystemExit("UI-R89 REV1 verifier failed: " + ", ".join(failed))
print("UI-R89 REV1 verifier PASS")
