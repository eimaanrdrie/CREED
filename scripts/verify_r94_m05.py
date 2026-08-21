from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MODELS = ROOT / "backend" / "app" / "domain" / "models.py"
ADVANCED = ROOT / "backend" / "app" / "services" / "advanced.py"
RUNS = ROOT / "backend" / "app" / "services" / "analysis_runs.py"
API = ROOT / "backend" / "app" / "api" / "advanced.py"
MIGRATION = ROOT / "backend" / "migrations" / "versions" / "e5f6a7b8c9d0_r94_m05_run_scoped_investigations.py"
TEST = ROOT / "backend" / "tests" / "test_r94_m05_run_scoped_reanalysis.py"


def require(text: str, needle: str) -> None:
    if needle not in text:
        raise SystemExit(f"FAIL: missing R94-M05 contract: {needle}")


def main() -> None:
    models = MODELS.read_text(encoding="utf-8")
    advanced = ADVANCED.read_text(encoding="utf-8")
    runs = RUNS.read_text(encoding="utf-8")
    api = API.read_text(encoding="utf-8")
    migration = MIGRATION.read_text(encoding="utf-8")
    test = TEST.read_text(encoding="utf-8")

    for needle in (
        'UniqueConstraint("agent_run_id", "implementation_id", name="uq_run_implementation_investigation")',
        'agent_run_id: Mapped[str | None] = mapped_column(ForeignKey("agent_runs.id", ondelete="SET NULL"), index=True)',
    ):
        require(models, needle)

    for needle in (
        "def investigations_for_run",
        "Investigation.agent_run_id == run_id",
        "InvestigationDetail.agent_run_id == run_id",
        "agent_run_id=run.id",
        "HumanDecision.investigation_id.in_(run_inv_ids)",
        "LearningProposalDetail.agent_run_id == run.id",
        "investigations=investigations_for_run(db, run.id)",
    ):
        require(advanced, needle)

    require(runs, "investigations_for_run(db, run.id)")

    for needle in (
        "rows=investigations_for_run(db,run.id)",
        "invs=investigations_for_run(db,run.id)",
        '"INVESTIGATION_NOT_IN_RUN"',
        "LearningProposalDetail.agent_run_id == run.id",
    ):
        require(api, needle)

    for needle in (
        'revision: str = "e5f6a7b8c9d0"',
        'down_revision: Union[str, None] = "h4c5d6e7f8g9"',
        'batch_op.drop_constraint("uq_issue_implementation_investigation"',
        '"uq_run_implementation_investigation"',
        "UPDATE investigations",
        "investigation_details.agent_run_id",
    ):
        require(migration, needle)

    for needle in (
        "test_normal_run_again_can_create_fresh_investigation_for_same_implementation",
        "test_run_endpoints_do_not_leak_prior_investigations_or_decisions",
        "test_human_review_rejects_investigation_from_another_run",
        "test_learning_proposal_lookup_is_run_scoped",
        "assert len(old.decisions) == 1",
        "assert len(new.decisions) == 1",
    ):
        require(test, needle)

    print("R94-M05 source contract: PASS")


if __name__ == "__main__":
    main()
