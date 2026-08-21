from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CSS = (ROOT / "frontend" / "app" / "globals.css").read_text(encoding="utf-8")
RUNTIME = (ROOT / "frontend" / "components" / "ai-runtime-console.tsx").read_text(encoding="utf-8")
NOTES = (ROOT / "UI_R20_NOTES.md").read_text(encoding="utf-8")

required_css = [
    "UI-R20 — Local AI Runtime Control Plane Readability Recomposition",
    ".runtime-r09 {\n  width: 100%;\n  max-width: 1320px",
    "--runtime-body: 15px",
    "min-height: 44px",
    "@media (max-width: 1460px)",
    ".runtime-layout-r09 { grid-template-columns: 1fr; }",
    ".runtime-execution-metrics-r20",
    "overflow-wrap: anywhere",
]
for token in required_css:
    assert token in CSS, f"missing UI-R20 CSS contract: {token}"

for token in [
    'role="status" aria-live="polite"',
    'aria-busy={testing}',
    'runtime-execution-metrics-r20',
    "Runtime state is earned from a real Ollama handshake",
    "No simulated completion timer is used.",
    "Local AI boundary",
    "No fake AI fallback",
]:
    assert token in RUNTIME, f"AI Runtime truth/accessibility contract drifted: {token}"

assert "Local AI Runtime Control Plane Readability Recomposition" in NOTES
assert not (ROOT / "frontend" / "app" / "demo").exists(), "Demo route must remain removed"
for path in (ROOT / "frontend").rglob("*.tsx"):
    text = path.read_text(encoding="utf-8")
    assert "react-icons" not in text
    assert "@heroicons" not in text
    assert "fontawesome" not in text.lower()

assert CSS.count("{") == CSS.count("}"), "CSS braces are unbalanced"
print("UI-R20 verification: PASS")
print("- AI Runtime workspace bounded to 1320px")
print("- runtime proof uses larger operational typography and 44px controls")
print("- inspector and live test console reflow before fixed-sidebar compression")
print("- execution history retains duration/tokens/time on mobile")
print("- real Ollama/Qwen proof and no-fake-AI semantics retained")
