from __future__ import annotations

import sys
from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from sqlalchemy import inspect, select

from app.db.session import get_engine, get_session_factory
from app.domain.models import DependencyEdge, Implementation, MethodVersion
from app.repositories.domain import DomainRepository

REQUIRED_TABLES = {
    "clients",
    "products",
    "modules",
    "support_issues",
    "evidence_documents",
    "delivery_methods",
    "method_versions",
    "implementations",
    "dependency_edges",
    "investigations",
    "findings",
    "human_decisions",
    "learning_proposals",
    "adoption_receipts",
    "recall_notices",
    "agent_runs",
    "agent_steps",
    "audit_events",
}


def fail(message: str) -> None:
    print(f"FAIL: {message}")
    raise SystemExit(1)


def main() -> None:
    try:
        engine = get_engine()
    except RuntimeError as exc:
        fail(str(exc))

    tables = set(inspect(engine).get_table_names())
    missing = REQUIRED_TABLES - tables
    if missing:
        fail(f"Missing M03 tables: {sorted(missing)}")

    with get_session_factory()() as session:
        counts = DomainRepository(session).summary_counts()
        versions = list(session.scalars(select(MethodVersion)))
        implementations = list(session.scalars(select(Implementation)))
        edges = list(session.scalars(select(DependencyEdge)))

    print(f"Tables verified: {len(REQUIRED_TABLES)}")
    print(f"Domain counts: {counts}")
    print(f"Method versions: {[(item.version, item.status) for item in versions]}")
    print(f"Implementations: {[item.name for item in implementations]}")
    print(f"Dependency edges: {len(edges)}")
    print("PASS: CREED M03 persistent domain model verified.")


if __name__ == "__main__":
    main()
