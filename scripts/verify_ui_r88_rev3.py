from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sidebar = (ROOT / "frontend/components/sidebar.tsx").read_text(encoding="utf-8")
design = (ROOT / "frontend/DESIGN.md").read_text(encoding="utf-8")

checks = {
    "hydration-safe initial label": 'useState(health?.timestamp ? "Latest health check" : "Checking live services")' in sidebar,
    "locale formatting deferred to effect": 'setCheckedAtLabel(`Checked ${checkedAt.toLocaleTimeString' in sidebar and '}, [health?.timestamp]);' in sidebar,
    "render uses stable state": '<span>{checkedAtLabel}</span>' in sidebar,
    "old SSR locale expression removed": 'new Date(health.timestamp).toLocaleTimeString' not in sidebar,
    "invalid timestamp fallback": 'Number.isNaN(checkedAt.valueOf())' in sidebar and 'setCheckedAtLabel("Latest health check")' in sidebar,
    "design contract": 'UI-R88 REV3 — Hydration-Safe System Health Timestamp' in design and 'must not depend on browser locale formatting' in design,
}

failed = [name for name, ok in checks.items() if not ok]
for name, ok in checks.items():
    print(f"{'PASS' if ok else 'FAIL'}  {name}")
if failed:
    raise SystemExit("UI-R88 REV3 verifier failed: " + ", ".join(failed))
print("UI-R88 REV3 verifier PASS")
