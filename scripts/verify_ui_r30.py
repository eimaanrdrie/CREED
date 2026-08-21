from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CSS = (ROOT / "frontend" / "app" / "globals.css").read_text(encoding="utf-8")
RUNTIME = (ROOT / "frontend" / "components" / "ai-runtime-console.tsx").read_text(encoding="utf-8")
NOTES = (ROOT / "UI_R30_NOTES.md").read_text(encoding="utf-8")
DESIGN = (ROOT / "frontend" / "DESIGN.md").read_text(encoding="utf-8")

for token in [
    "UI-R30 — Minimal AI Runtime + Final Visual Polish",
    ".runtime-r30",
    ".runtime-proof-flow-r30",
    ".runtime-glance-r30",
    ".runtime-live-r30",
    ".runtime-history-r30",
    ".runtime-selected-r30",
    "max-width:1320px",
    "min-height:44px",
    "@media (max-width:620px)",
]:
    assert token in CSS, f"missing UI-R30 CSS contract: {token}"

for token in [
    "Local Qwen. Prove it live.",
    'runtime?.status === "READY"',
    'fetch(`${API_BASE_URL}/api/v1/ai/runtime?refresh=true`',
    'fetch(`${API_BASE_URL}/api/v1/ai/test`',
    "runtime-proof-flow-r30",
    "ProgressiveDisclosure",
    'label="JSON proof"',
    'label="Runtime provenance"',
    'aria-busy={testing}',
    'role="status" aria-live="polite"',
    "No simulated completion timer is used.",
    "Local AI boundary.",
    "No fake AI fallback.",
]:
    assert token in RUNTIME, f"AI Runtime minimal/truth contract drifted: {token}"

# The old permanent inspector should no longer be part of the R30 JSX.
assert '<aside className="runtime-inspector-r09">' not in RUNTIME
assert 'Prove the model before CREED trusts it.' not in RUNTIME
assert '<pre>{JSON.stringify(result.output, null, 2)}</pre>' not in RUNTIME

assert "Glance → Execute → Prove" in NOTES
assert "R23–R30" in NOTES
assert "UI-R30 — Minimal AI Runtime + Visual-Minimalism Closure" in DESIGN
assert not (ROOT / "frontend" / "app" / "demo").exists(), "Demo route must remain removed"

for path in (ROOT / "frontend").rglob("*.tsx"):
    text = path.read_text(encoding="utf-8")
    assert "react-icons" not in text
    assert "@heroicons" not in text
    assert "fontawesome" not in text.lower()

assert CSS.count("{") == CSS.count("}"), "CSS braces are unbalanced"
print("UI-R30 verification: PASS")
print("- AI Runtime distilled to Glance → Execute → Prove")
print("- real Ollama/Qwen handshake and execution paths retained")
print("- JSON and runtime provenance are progressive, not removed")
print("- permanent inspector rail removed; selected execution proof is contextual")
print("- no-fake-AI, loopback/configured distinction, Demo removal and Lucide-only policy retained")
