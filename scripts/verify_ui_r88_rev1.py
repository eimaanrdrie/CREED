from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sidebar = (ROOT / "frontend/components/sidebar.tsx").read_text(encoding="utf-8")
css = (ROOT / "frontend/app/globals.css").read_text(encoding="utf-8")
design = (ROOT / "frontend/DESIGN.md").read_text(encoding="utf-8")

checks = {
    "daily assurance first level": all(token in sidebar for token in [
        'CORE_NAV_ITEMS',
        '{ label: "Overview", icon: LayoutDashboard, href: "/" }',
        '{ label: "Issues", icon: FileWarning, href: "/issues" }',
        '{ label: "Change Radar", icon: Radar, href: "/change-radar" }',
        '{ label: "Knowledge", icon: LibraryBig, href: "/knowledge" }',
        '{ label: "Recalls", icon: History, href: "/recalls" }',
    ]),
    "registry grouping": 'REGISTRY_NAV_ITEMS' in sidebar and 'label="Registry"' in sidebar and 'Icon={Layers3}' in sidebar,
    "governance grouping": 'GOVERNANCE_NAV_ITEMS' in sidebar and 'label="Governance"' in sidebar and 'Icon={Scale}' in sidebar,
    "audit moved under governance": '{ label: "Audit", icon: Activity, href: "/audit" }' in sidebar and 'GOVERNANCE_NAV_ITEMS' in sidebar,
    "ai runtime utility": 'UTILITY_NAV_ITEMS' in sidebar and 'className="nav nav-utility"' in sidebar,
    "accessible disclosure": all(token in sidebar for token in ['aria-expanded={open}', 'aria-controls={controlId}', 'hidden={!open}']),
    "active group auto open": 'setRegistryOpen(registryContainsActive)' in sidebar and 'setGovernanceOpen(governanceContainsActive)' in sidebar,
    "children keep page state": 'aria-current={active ? "page" : undefined}' in sidebar,
    "lucide only": 'from "lucide-react"' in sidebar and 'ChevronRight' in sidebar and 'Layers3' in sidebar and 'Scale' in sidebar,
    "distilled nested styling": '.nav-group-toggle' in css and '.nav-item-child' in css and '.nav-utility' in css,
    "bounded short-height fallback": 'overflow-y:auto' in css and 'scrollbar-width:thin' in css,
    "reduced motion": '@media (prefers-reduced-motion:reduce)' in css and '.nav-group-toggle .nav-group-chevron' in css,
    "design contract": 'UI-R88 REV1 — Sidebar Information Architecture' in design and 'Registry (collapsible)' in design and 'Governance (collapsible)' in design,
    "demo route still excluded": 'There is no Demo tab or Demo route' in design,
}

failed = [name for name, ok in checks.items() if not ok]
for name, ok in checks.items():
    print(f"{'PASS' if ok else 'FAIL'}  {name}")
if failed:
    raise SystemExit("UI-R88 REV1 verifier failed: " + ", ".join(failed))
print("UI-R88 REV1 verifier PASS")
