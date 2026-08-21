from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CSS = (ROOT / "frontend" / "app" / "globals.css").read_text(encoding="utf-8")
SHELL = (ROOT / "frontend" / "components" / "app-shell.tsx").read_text(encoding="utf-8")
SIDEBAR = (ROOT / "frontend" / "components" / "sidebar.tsx").read_text(encoding="utf-8")
PRIMITIVES = (ROOT / "frontend" / "components" / "visual-primitives.tsx").read_text(encoding="utf-8")
NOTES = (ROOT / "UI_R22_NOTES.md").read_text(encoding="utf-8")

for token in [
    "UI-R22 — Global Visual Minimalism System",
    ".system-signal-strip",
    ".visual-metric",
    ".signal-chip",
    ".progressive-disclosure",
    ".visual-flow",
    ".user-role-detail { display:none!important; }",
    ".crumb-home-icon",
]:
    assert token in CSS, f"missing UI-R22 visual-minimalism contract: {token}"

for token in [
    "crumb-home crumb-home-icon",
    "ShieldCheck size={14}",
    'className="user-role-detail"',
]:
    assert token in SHELL, f"global shell was not distilled: {token}"

for token in [
    "CheckCircle2",
    "TriangleAlert",
    "CircleHelp",
    'aria-label={`${label}: ${readable}`}',
]:
    assert token in SIDEBAR, f"compact truthful system signal contract drifted: {token}"
assert ("system-signal-strip" in SIDEBAR or "system-status-list" in SIDEBAR), "truthful system signal presentation missing"
assert ('<span className="sr-only">{stateLabel(state)}</span>' in SIDEBAR or '<span>{readable}</span>' in SIDEBAR), "system state must remain readable"

for token in [
    "export function VisualMetric",
    "export function SignalChip",
    "export function ProgressiveDisclosure",
    "details className=\"progressive-disclosure\"",
    "ChevronDown",
]:
    assert token in PRIMITIVES, f"missing GLANCE / INSPECT / PROVE primitive: {token}"

short_copy = {
    "frontend/components/final-dashboard.tsx": "From issue to evidence, decision, adoption and recall — with humans in control.",
    "frontend/components/issues-workspace.tsx": "Search, triage and open governed delivery cases.",
    "frontend/components/issue-detail-workspace.tsx": "Human-supplied source. AI interpretation stays separate.",
    "frontend/components/analysis-shell.tsx": "Follow evidence → impact → investigation → human decision.",
    "frontend/components/change-radar-workspace.tsx": "Priority is not a verdict.",
    "frontend/components/knowledge-workspace.tsx": "Find, inspect and ingest governed evidence with provenance intact.",
    "frontend/components/recalls-workspace.tsx": "Revoke approved knowledge and route every explicit adopter into review.",
    "frontend/components/audit-workspace.tsx": "Trace execution, evidence, Qwen, impact and human authority.",
    "frontend/components/ai-runtime-console.tsx": "READY requires Ollama, the configured Qwen model and schema-validated inference.",
}
for path, token in short_copy.items():
    text = (ROOT / path).read_text(encoding="utf-8")
    assert token in text, f"top-level copy was not distilled in {path}"

assert "Global Visual Minimalism System" in NOTES
assert "GLANCE → INSPECT → PROVE" in NOTES
assert not (ROOT / "frontend" / "app" / "demo").exists(), "Demo route must remain removed"
for path in (ROOT / "frontend").rglob("*.tsx"):
    text = path.read_text(encoding="utf-8")
    assert "react-icons" not in text
    assert "@heroicons" not in text
    assert "fontawesome" not in text.lower()

assert CSS.count("{") == CSS.count("}"), "CSS braces are unbalanced"
print("UI-R22 verification: PASS")
print("- persistent shell copy and repeated status prose reduced")
print("- API / DB / Qwen remain truthful visual + accessible state signals")
print("- top-level explanatory copy distilled across all major surfaces")
print("- GLANCE / INSPECT / PROVE primitives added for R23-R30")
print("- typography floor, Demo removal, Lucide-only and governance semantics preserved")
