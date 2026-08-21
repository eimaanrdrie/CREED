from pathlib import Path

root = Path(__file__).resolve().parents[1]
dashboard = (root / "frontend/components/final-dashboard.tsx").read_text(encoding="utf-8")
radar = (root / "frontend/components/change-radar-workspace.tsx").read_text(encoding="utf-8")
css = (root / "frontend/app/globals.css").read_text(encoding="utf-8")
checks = {
    "overview no contextless radar link": 'href: "/change-radar"' not in dashboard and 'View radar' not in dashboard,
    "approved knowledge signal": 'label: "Approved knowledge"' in dashboard and 'href: "/approved-knowledge"' in dashboard,
    "human review wording": 'label: "Human review"' in dashboard,
    "recall wording": 'meta: "recall notices"' in dashboard,
    "updated lifecycle subtitle": 'Issue → evidence → investigation → human → learning → recall.' in dashboard,
    "investigation flow": 'label: "Investigation"' in dashboard and 'active_investigations' in dashboard,
    "knowledge flow": 'label: "Knowledge"' in dashboard and 'approved_method_versions' in dashboard,
    "six step layout": 'grid-template-columns:repeat(6,minmax(0,1fr))' in css,
    "registry coverage link": 'href: "/dependencies"' in dashboard,
    "methods link": 'href="/methods"' in dashboard,
    "radar router": 'useRouter' in radar and 'const router = useRouter()' in radar,
    "radar back button": 'radar-back-r99-m06' in radar and 'router.back()' in radar and '>Back<' not in radar,
    "radar back css": '.radar-back-r99-m06' in css,
}
failed = [name for name, ok in checks.items() if not ok]
for name, ok in checks.items():
    print(("PASS" if ok else "FAIL"), name)
if failed:
    raise SystemExit("UI-R99-M06 verification failed: " + ", ".join(failed))
print("UI-R99-M06 PASS")
