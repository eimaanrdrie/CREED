from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CSS = (ROOT / "frontend/app/globals.css").read_text(encoding="utf-8")
DESIGN = (ROOT / "frontend/DESIGN.md").read_text(encoding="utf-8")
NOTES = (ROOT / "UI_R74_NOTES.md").read_text(encoding="utf-8")
ANALYSIS = (ROOT / "frontend/components/analysis-shell.tsx").read_text(encoding="utf-8")
RUNTIME = (ROOT / "frontend/components/ai-runtime-console.tsx").read_text(encoding="utf-8")
AUDIT = (ROOT / "frontend/components/audit-workspace.tsx").read_text(encoding="utf-8")
SIDEBAR = (ROOT / "frontend/components/sidebar.tsx").read_text(encoding="utf-8")

marker = "/* UI-R74 — Off-White Palette Migration"
assert marker in CSS, "Missing R74 palette block"
r74_css = CSS.split(marker, 1)[1]

palette = {
    "--creed-background": "#071019",
    "--creed-surface": "#0B1724",
    "--creed-raised": "#102033",
    "--creed-off-white": "#F3EDE3",
    "--creed-secondary": "#A8B5C3",
    "--creed-muted": "#7D8A98",
    "--creed-hairline": "#1B2A3A",
    "--creed-action": "#7CC7D9",
    "--creed-success": "#6FBF9E",
    "--creed-warning": "#D6A86B",
    "--creed-danger": "#C96B6B",
}
for token, value in palette.items():
    assert f"{token}: {value};" in r74_css, f"Missing exact R74 token {token}={value}"

for contract in [
    "--text: var(--creed-off-white);",
    "--text-soft: var(--creed-secondary);",
    "--text-muted: var(--creed-muted);",
    "--line: var(--creed-hairline);",
    "--azure: var(--creed-action);",
    "--azure-pale: var(--creed-off-white);",
    "--trusted: var(--creed-success);",
    "--amber: var(--creed-warning);",
    "--red: var(--creed-danger);",
    "--gold: var(--creed-action);",
    "--gold-pale: var(--creed-off-white);",
    "--verdigris: var(--creed-success);",
    ".nav-primary .nav-item.active {",
    ".runtime-execution-r30.selected {",
    ".audit-filter-row-r29 button.active {",
    ".analysis-r69 {",
]:
    assert contract in r74_css, f"Missing R74 compatibility/semantic contract: {contract}"

# R74 must be palette only and preserve the approved R71-R73 source contracts.
for token in [
    "/* UI-R71 — Remove Hero Eyebrows + Decorative Pill Chips",
    "/* UI-R72 — Sidebar Active-State / Accent Cleanup",
    "/* UI-R73 — AI Runtime / Execution Proof Alignment Correction",
    "--runtime-proof-rail-r73: 18px;",
    ".runtime-selected-glance-r30 {",
]:
    assert token in CSS, f"R74 regressed approved source contract: {token}"

# Runtime truth remains wired to real API/persisted execution values.
for token in [
    'fetch(`${API_BASE_URL}/api/v1/ai/runtime?refresh=true`',
    'fetch(`${API_BASE_URL}/api/v1/ai/test`',
    'runtime?.recent_executions',
    'selectedExecution.duration_ms',
    'selectedExecution.prompt_eval_count',
    'selectedExecution.eval_count',
    'selectedExecution.structured_output_valid',
]:
    assert token in RUNTIME, f"R74 lost real runtime contract: {token}"

# Approved Analysis + Human Review interrupt/resume semantics remain intact.
for token in [
    "AnalysisWorkspaceNavigator",
    "Case Context",
    "Evidence",
    "Investigation",
    "Human Decision",
    "<h2>Agent Execution Task</h2>",
    "startAnalysisRun(issue.id)",
    "runIssueUnderstanding(issue.id)",
    "analysisRunEventsUrl(run.graph_run_id",
    "resumeHumanReview(run.graph_run_id",
]:
    assert token in ANALYSIS, f"R74 regressed Analysis/governance contract: {token}"
assert "analysis-path-r55 { display:none!important; }" in CSS

# R48 Audit pagination and navigation/icon policies remain intact.
assert "const AUDIT_PAGE_SIZE = 6" in AUDIT
assert "audit-pagination-r48" in AUDIT
assert 'aria-current={active === label ? "page" : undefined}' in SIDEBAR
assert not (ROOT / "frontend/app/demo").exists(), "Demo route must remain removed"
for path in (ROOT / "frontend").rglob("*.tsx"):
    source = path.read_text(encoding="utf-8")
    assert "<svg" not in source.lower(), f"Raw SVG found in {path}"
    assert "react-icons" not in source
    assert "@heroicons" not in source
    assert "fontawesome" not in source.lower()

# WCAG contrast check for the exact palette on the darkest approved surfaces.
def srgb_channel(v: int) -> float:
    x = v / 255.0
    return x / 12.92 if x <= 0.04045 else ((x + 0.055) / 1.055) ** 2.4

def luminance(hex_value: str) -> float:
    s = hex_value.lstrip("#")
    r, g, b = (int(s[i:i+2], 16) for i in (0, 2, 4))
    return 0.2126 * srgb_channel(r) + 0.7152 * srgb_channel(g) + 0.0722 * srgb_channel(b)

def contrast(a: str, b: str) -> float:
    hi, lo = sorted((luminance(a), luminance(b)), reverse=True)
    return (hi + 0.05) / (lo + 0.05)

values = {k: v for k, v in palette.items()}
for fg in ["--creed-off-white", "--creed-secondary", "--creed-muted", "--creed-action", "--creed-success", "--creed-warning", "--creed-danger"]:
    ratio = contrast(values[fg], values["--creed-raised"])
    assert ratio >= 4.5, f"R74 contrast below 4.5:1 for {fg} on raised surface: {ratio:.2f}"
assert contrast(values["--creed-background"], values["--creed-action"]) >= 4.5

assert "## UI-R74 — Off-White Palette Migration" in DESIGN
assert "R75 remains" in DESIGN
assert "No R75 exhaustive theme-consistency sweep" in NOTES
assert CSS.count("{") == CSS.count("}"), "CSS braces are unbalanced"

print("UI-R74 verifier: PASS")
print("- exact off-white-led palette tokens are present")
print("- text/action/status compatibility aliases resolve to R74 tokens")
print("- exact palette colors meet >=4.5:1 contrast on raised surface")
print("- R71-R73, Analysis, runtime truth, governance, Audit pagination and Demo removal preserved")
print("- exhaustive component-local consistency remains reserved for R75")
