from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ADVANCED = ROOT / "backend" / "app" / "services" / "advanced.py"
RUNS = ROOT / "backend" / "app" / "services" / "analysis_runs.py"
TEST = ROOT / "backend" / "tests" / "test_r94_m03_robust_catalog_resolution.py"


def require(text: str, needle: str) -> None:
    if needle not in text:
        raise SystemExit(f"FAIL: missing R94-M03 contract: {needle}")


def main() -> None:
    advanced = ADVANCED.read_text(encoding="utf-8")
    runs = RUNS.read_text(encoding="utf-8")
    test = TEST.read_text(encoding="utf-8")

    for needle in (
        "def _catalog_tokens",
        "def _catalog_acronym",
        "def _unique_catalog_match",
        '"CANONICAL_EXACT"',
        '"ACRONYM"',
        '"CATALOG_PHRASE"',
        '"REPORTED_CLIENT_UNIQUE_MODULE"',
        "def resolve_catalog_context",
        "def _unique_abom_method_version_for_module",
        '"MODULE_ABOM_UNIQUE_VERSION"',
        '"routing":routing',
    ):
        require(advanced, needle)

    for needle in (
        "resolve_catalog_context",
        'routing=result.get("routing") or {}',
        '"routing":routing',
    ):
        require(runs, needle)

    for needle in (
        "test_hyphen_insensitive_module_name_routes_registered_implementations",
        "test_ptp_acronym_resolves_only_when_unique",
        "test_longer_qwen_phrase_resolves_catalog_module",
        "test_ambiguous_acronym_fails_closed_without_client_anchor",
        "test_reported_client_unique_registered_module_is_safe_fallback",
        'assert result["routing"]["strategy"] == "MODULE_ABOM_UNIQUE_VERSION"',
    ):
        require(test, needle)

    print("R94-M03 source contract: PASS")


if __name__ == "__main__":
    main()
