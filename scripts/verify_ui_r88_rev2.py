from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sidebar = (ROOT / "frontend/components/sidebar.tsx").read_text(encoding="utf-8")
css = (ROOT / "frontend/app/globals.css").read_text(encoding="utf-8")
design = (ROOT / "frontend/DESIGN.md").read_text(encoding="utf-8")
r88_css = css.split("/* UI-R88 REV2 — No-scroll sidebar information architecture", 1)[1]

checks = {
    "daily assurance remains first level": all(token in sidebar for token in [
        '{ label: "Overview", icon: LayoutDashboard, href: "/" }',
        '{ label: "Issues", icon: FileWarning, href: "/issues" }',
        '{ label: "Change Radar", icon: Radar, href: "/change-radar" }',
        '{ label: "Knowledge", icon: LibraryBig, href: "/knowledge" }',
        '{ label: "Recalls", icon: History, href: "/recalls" }',
    ]),
    "registry flyout grouping": 'NavigationFlyoutGroup' in sidebar and 'label="Registry"' in sidebar and 'REGISTRY_NAV_ITEMS' in sidebar,
    "governance flyout grouping": 'label="Governance"' in sidebar and 'GOVERNANCE_NAV_ITEMS' in sidebar,
    "no inline child navigation": 'nav-item-child' not in sidebar and 'nav-group-panel' not in sidebar,
    "active parent context": 'nav-group-current' in sidebar and 'contains-active' in sidebar and 'active-parent' in sidebar,
    "contextual descriptions": 'NAV_DESCRIPTIONS' in sidebar and 'Local A-BOM relationships' in sidebar and 'Traceable activity history' in sidebar,
    "accessible flyout controls": all(token in sidebar for token in [
        'aria-expanded={open}', 'aria-controls={controlId}', 'hidden={!open}', 'aria-current={active ? "page" : undefined}'
    ]),
    "escape and outside close": 'event.key === "Escape"' in sidebar and 'pointerdown' in sidebar and 'sidebar.contains' in sidebar,
    "system distilled": 'systemSummary(health)' in sidebar and 'system-summary-btn' in sidebar and 'system-health-popover' in sidebar,
    "truthful service detail": all(token in sidebar for token in [
        'health?.dependencies.api', 'health?.dependencies.database', 'health?.dependencies.qwen', 'health?.dependencies.knowledge_source'
    ]),
    "system runtime path": 'href="/ai-runtime"' in sidebar and 'View AI Runtime' in sidebar,
    "desktop nav no scroll region": 'overflow:visible;' in r88_css and '.nav-primary {' in r88_css and 'scrollbar-width' not in r88_css,
    "short height preserves touch floor": '@media (max-height:700px) and (min-width:761px)' in r88_css and '.nav-item { min-height:44px; }' in r88_css,
    "mobile overlay not nested rows": '.sidebar-mobile .nav-flyout' in r88_css and 'position:absolute;' in r88_css and 'max-height:calc(100% - 96px)' in r88_css,
    "reduced motion": '@media (prefers-reduced-motion:reduce)' in r88_css and '.system-summary-chevron' in r88_css,
    "lucide only": 'from "lucide-react"' in sidebar and 'Layers3' in sidebar and 'Scale' in sidebar,
    "design contract": 'UI-R88 REV2 — No-Scroll Sidebar' in design and 'children no longer expand inline on desktop' in design and 'does not use an internal scrollbar' in design,
    "demo policy retained": 'Demo-route exclusion remain unchanged' in design,
}

failed = [name for name, ok in checks.items() if not ok]
for name, ok in checks.items():
    print(f"{'PASS' if ok else 'FAIL'}  {name}")
if failed:
    raise SystemExit("UI-R88 REV2 verifier failed: " + ", ".join(failed))
print("UI-R88 REV2 verifier PASS")
