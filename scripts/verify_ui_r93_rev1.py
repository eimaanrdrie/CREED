from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
sidebar = (ROOT / "frontend/components/sidebar.tsx").read_text(encoding="utf-8")
css = (ROOT / "frontend/app/globals.css").read_text(encoding="utf-8")
design = (ROOT / "frontend/DESIGN.md").read_text(encoding="utf-8")
notes = (ROOT / "UI_R93_REV1_NOTES.md").read_text(encoding="utf-8")
runtime_page = (ROOT / "frontend/app/ai-runtime/page.tsx").read_text(encoding="utf-8")
runtime_console = (ROOT / "frontend/components/ai-runtime-console.tsx").read_text(encoding="utf-8")

ai_route_mentions = re.findall(r'href:\s*"/ai-runtime"|href="/ai-runtime"', sidebar)
health_block = sidebar.split('<div className="system-health-popover"', 1)[1].split('</div>\n      </div>\n    </aside>', 1)[0]

checks = {
    "exactly one shell AI Runtime destination": len(ai_route_mentions) == 1,
    "utility AI Runtime retained": '{ label: "AI Runtime", icon: BrainCircuit, href: "/ai-runtime" }' in sidebar,
    "system health duplicate removed": 'View AI Runtime' not in sidebar and 'system-health-link' not in sidebar,
    "system health has no runtime route": '/ai-runtime' not in health_block,
    "four health services only": all(token in sidebar for token in [
        '["API", health?.dependencies.api, Server]',
        '["Database", health?.dependencies.database, Database]',
        '["Qwen", health?.dependencies.qwen, BrainCircuit]',
        '["Knowledge Source", health?.dependencies.knowledge_source, LibraryBig]',
    ]),
    "health row source remains status-only": 'system-health-list' in sidebar and 'statuses.map' in sidebar,
    "dead health-link css removed": '.system-health-link' not in css,
    "AI runtime route preserved": 'AiRuntimeConsole' in runtime_page and 'active="AI Runtime"' in runtime_page,
    "runtime behavior wiring preserved": all(token in runtime_console for token in [
        'fetch(`${API_BASE_URL}/api/v1/ai/runtime?refresh=true`',
        'fetch(`${API_BASE_URL}/api/v1/ai/test`',
        'runtime?.recent_executions',
        'runtime?.status === "READY"',
    ]),
    "R92 flyout contract preserved": all(token in sidebar for token in [
        'nav-flyout-bridge-r92',
        '}, 280);',
        'lockedPanelRef',
        'scheduleFlyoutClose',
    ]),
    "semantic distinction documented": 'System answers **“Is CREED healthy?”**' in design and 'AI Runtime remains the single primary shell destination' in design,
    "notes candidate": 'Status: candidate, awaiting user approval.' in notes and 'Frontend shell navigation/presentation only.' in notes,
}

failed = [name for name, ok in checks.items() if not ok]
for name, ok in checks.items():
    print(f"{'PASS' if ok else 'FAIL'}  {name}")
if failed:
    raise SystemExit("UI-R93 REV1 verifier failed: " + ", ".join(failed))
print("UI-R93 REV1 verifier PASS")
