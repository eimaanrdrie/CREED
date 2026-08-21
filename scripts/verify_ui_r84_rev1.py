from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
api = (ROOT / "frontend/lib/api.ts").read_text(encoding="utf-8")
sidebar = (ROOT / "frontend/components/sidebar.tsx").read_text(encoding="utf-8")
page = (ROOT / "frontend/app/authority/page.tsx").read_text(encoding="utf-8")
workspace = (ROOT / "frontend/components/human-authority-workspace.tsx").read_text(encoding="utf-8")
css = (ROOT / "frontend/app/globals.css").read_text(encoding="utf-8")
models = (ROOT / "backend/app/domain/models.py").read_text(encoding="utf-8")
domain_api = (ROOT / "backend/app/api/domain.py").read_text(encoding="utf-8")
domain_service = (ROOT / "backend/app/services/domain.py").read_text(encoding="utf-8")
repo = (ROOT / "backend/app/repositories/domain.py").read_text(encoding="utf-8")
migration = (ROOT / "backend/migrations/versions/d0e1f2a3b4c5_r84_human_authority_registry.py").read_text(encoding="utf-8")

checks = {
    "authority route": 'active="Authority"' in page and "HumanAuthorityWorkspace" in page,
    "authority nav": '{ label: "Authority", icon: UserRoundCheck, href: "/authority" }' in sidebar,
    "persistent authority model": 'class HumanAuthority(Base, TimestampMixin)' in models and '__tablename__ = "human_authorities"' in models,
    "schema migration": 'down_revision: Union[str, None] = "cfd6e75baf98"' in migration and 'op.create_table(' in migration and '"human_authorities"' in migration,
    "real list/create/update API": '/api/v1/domain/authorities' in api and 'createHumanAuthority' in api and 'updateHumanAuthority' in api,
    "backend endpoints": '@router.get("/authorities"' in domain_api and '@router.post("/authorities"' in domain_api and '@router.patch("/authorities/{authority_id}"' in domain_api,
    "stable principal": 'principal: Mapped[str]' in models and 'AUTHORITY_PRINCIPAL_ALREADY_EXISTS' in domain_service,
    "governed permissions": 'can_submit_human_decision' in models and 'can_approve_learning' in models and 'can_authorize_recall' in models,
    "audited registration/update": 'action="HUMAN_AUTHORITY_REGISTERED"' in domain_service and 'action="HUMAN_AUTHORITY_UPDATED"' in domain_service,
    "repository helpers": 'def get_human_authority_by_principal' in repo and 'def list_human_authorities' in repo,
    "no authentication claim": 'identity authentication remains outside this registry' in workspace,
    "runtime enforcement progression": 'CREED now enforces these permissions' in workspace,
    "principal immutable in UI": 'Principal is immutable' in workspace and 'cannot be edited after registration' in workspace,
    "real error state": 'No placeholder principals are being shown' in workspace,
    "lucide icons": 'from "lucide-react"' in workspace and 'UserRoundCheck' in sidebar,
    "scoped styles": '.authority-registry-r84' in css and '.authority-edit-r84' in css,
    "responsive hardening": '@media (max-width:560px)' in css and '.authority-row-r84 { grid-template-columns:1fr; }' in css,
}

failures = [name for name, passed in checks.items() if not passed]
for name, passed in checks.items():
    print(f"{'PASS' if passed else 'FAIL'}  {name}")
if failures:
    raise SystemExit("UI-R84 REV1 verification failed: " + ", ".join(failures))
print("UI-R84 REV1 verifier PASS")
