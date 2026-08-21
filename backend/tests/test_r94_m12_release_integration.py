from __future__ import annotations

from pathlib import Path

from app.services.demo import DOC_META, _demo_dir


def test_final_release_packages_every_demo_reset_and_recall_asset():
    demo_dir = _demo_dir()
    missing = [name for name in DOC_META if not (demo_dir / name).is_file()]
    assert missing == []
    assert (demo_dir / "RECALL-PTP-V2-001.md").is_file()


def test_backend_docker_image_copies_demo_assets_required_by_operator_route():
    backend_root = Path(__file__).resolve().parents[1]
    dockerfile = (backend_root / "Dockerfile").read_text(encoding="utf-8")
    assert "COPY demo_data ./demo_data" in dockerfile
