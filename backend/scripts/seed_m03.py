from __future__ import annotations

import sys
from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from sqlalchemy import select

from app.db.session import get_session_factory
from app.domain.enums import MethodVersionStatus
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


def seed() -> None:
    factory = get_session_factory()
    with factory() as session:
        service = DomainService(session)

        atlas = service.create_client(name="Atlas Bank", actor="seed-m03")
        meridian = service.create_client(name="Meridian Bank", actor="seed-m03")
        nova = service.create_client(name="Nova Finance", client_type="FINANCIAL_INSTITUTION", actor="seed-m03")
        product = service.create_product(
            name="Collections",
            description="Synthetic collections product used by the CREED MVP.",
            actor="seed-m03",
        )
        module = service.create_module(
            product=product,
            name="Promise-to-Pay",
            description="Synthetic PTP module for demonstrating delivery knowledge relationships.",
            actor="seed-m03",
        )

        method = session.scalar(select(DeliveryMethod).where(DeliveryMethod.module_id == module.id, DeliveryMethod.name == "PTP Event Handling"))
        if method is None:
            method = DeliveryMethod(
                module_id=module.id,
                name="PTP Event Handling",
                description="Synthetic reusable event-processing delivery method.",
            )
            session.add(method)
            session.flush()
            session.add(AuditEvent(actor="seed-m03", action="METHOD_CREATED", object_type="DeliveryMethod", object_id=method.id, metadata_json={"name": method.name}))

        version = session.scalar(select(MethodVersion).where(MethodVersion.method_id == method.id, MethodVersion.version == "PTP-EVENT-v1"))
        if version is None:
            version = MethodVersion(method_id=method.id, version="PTP-EVENT-v1", status=MethodVersionStatus.APPROVED.value, summary="Synthetic baseline PTP event method.")
            session.add(version)
            session.flush()

        for client in (atlas, meridian, nova):
            implementation = session.scalar(
                select(Implementation).where(
                    Implementation.client_id == client.id,
                    Implementation.module_id == module.id,
                    Implementation.release_version == "R1",
                )
            )
            if implementation is None:
                implementation = Implementation(
                    client_id=client.id,
                    product_id=product.id,
                    module_id=module.id,
                    name=f"{client.name} Collections PTP",
                    release_version="R1",
                    metadata_json={"synthetic": True},
                )
                session.add(implementation)
                session.flush()

            edge = session.scalar(
                select(DependencyEdge).where(
                    DependencyEdge.source_type == "Implementation",
                    DependencyEdge.source_id == implementation.id,
                    DependencyEdge.target_type == "MethodVersion",
                    DependencyEdge.target_id == version.id,
                    DependencyEdge.relationship == "USES_METHOD_VERSION",
                )
            )
            if edge is None:
                session.add(
                    DependencyEdge(
                        source_type="Implementation",
                        source_id=implementation.id,
                        target_type="MethodVersion",
                        target_id=version.id,
                        relationship="USES_METHOD_VERSION",
                        confidence=1.0,
                    )
                )

        session.commit()
        print("M03 seed complete: Atlas Bank, Meridian Bank, Nova Finance, Collections, Promise-to-Pay, PTP-EVENT-v1.")


if __name__ == "__main__":
    seed()
