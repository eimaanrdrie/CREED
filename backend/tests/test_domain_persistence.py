from pathlib import Path

from sqlalchemy import create_engine, inspect, select
from sqlalchemy.orm import sessionmaker

from app.db.base import Base
from app.domain.models import (
    AuditEvent,
    Client,
    DeliveryMethod,
    DependencyEdge,
    Implementation,
    MethodVersion,
    Module,
    Product,
)
from app.services.domain import DomainService


def make_session(tmp_path: Path):
    db_path = tmp_path / "creed-domain.db"
    engine = create_engine(f"sqlite:///{db_path}")
    Base.metadata.create_all(engine)
    return engine, sessionmaker(bind=engine, expire_on_commit=False)


def test_domain_schema_contains_required_m03_tables(tmp_path):
    engine, _ = make_session(tmp_path)
    tables = set(inspect(engine).get_table_names())
    required = {
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
    assert required.issubset(tables)


def test_service_persists_client_product_module_and_audit(tmp_path):
    engine, factory = make_session(tmp_path)
    with factory() as session:
        service = DomainService(session)
        client = service.create_client(name="Atlas Bank", actor="test")
        product = service.create_product(name="Collections", actor="test")
        module = service.create_module(product=product, name="Promise-to-Pay", actor="test")
        service.commit()
        ids = (client.id, product.id, module.id)

    with factory() as session:
        assert session.get(Client, ids[0]).name == "Atlas Bank"
        assert session.get(Product, ids[1]).name == "Collections"
        assert session.get(Module, ids[2]).name == "Promise-to-Pay"
        assert len(list(session.scalars(select(AuditEvent)))) == 3
    engine.dispose()


def test_local_abom_dependency_edge_is_persistent(tmp_path):
    engine, factory = make_session(tmp_path)
    with factory() as session:
        client = Client(name="Meridian Bank")
        product = Product(name="Collections")
        session.add_all([client, product])
        session.flush()
        module = Module(product_id=product.id, name="Promise-to-Pay")
        session.add(module)
        session.flush()
        method = DeliveryMethod(module_id=module.id, name="PTP Event Handling")
        session.add(method)
        session.flush()
        version = MethodVersion(method_id=method.id, version="PTP-EVENT-v1", status="APPROVED")
        implementation = Implementation(
            client_id=client.id,
            product_id=product.id,
            module_id=module.id,
            name="Meridian PTP",
            release_version="R1",
        )
        session.add_all([version, implementation])
        session.flush()
        edge = DependencyEdge(
            source_type="Implementation",
            source_id=implementation.id,
            target_type="MethodVersion",
            target_id=version.id,
            relationship="USES_METHOD_VERSION",
            confidence=1.0,
        )
        session.add(edge)
        session.commit()
        edge_id = edge.id

    with factory() as session:
        persisted = session.get(DependencyEdge, edge_id)
        assert persisted is not None
        assert persisted.relationship == "USES_METHOD_VERSION"
        assert persisted.confidence == 1.0
    engine.dispose()
