from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
css = (ROOT / "frontend/app/globals.css").read_text(encoding="utf-8")
notes = (ROOT / "UI_R41_NOTES.md").read_text(encoding="utf-8")

checks = {
    "r41 marker": "UI-R41 — AI Runtime panel alignment + proof rhythm" in css,
    "shared runtime rail": ".runtime-history-head-r30,\n.runtime-execution-r30,\n.runtime-selected-r30" in css,
    "runtime provenance full border": ".runtime-selected-r30 > .progressive-disclosure" in css and "border:1px solid var(--line);" in css,
    "open disclosure divider": ".runtime-selected-r30 > .progressive-disclosure[open] > summary" in css,
    "notes": "AI Runtime Panel Alignment + Proof Rhythm" in notes,
}
failed = [name for name, ok in checks.items() if not ok]
if failed:
    raise SystemExit("UI-R41 verification failed: " + ", ".join(failed))
print("UI-R41 verifier: PASS")
