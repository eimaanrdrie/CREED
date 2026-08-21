from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.api.domain import get_domain_db
from app.db.base import Base
from app.main import app


@pytest.fixture
def client(tmp_path: Path):
    engine = create_engine(f"sqlite:///{tmp_path / 'api.db'}", connect_args={"check_same_thread": False})
    Base.metadata.create_all(engine)
    factory = sessionmaker(bind=engine, expire_on_commit=False)

    def override_db():
        with factory() as session:
            yield session

    app.dependency_overrides[get_domain_db] = override_db
    try:
        yield TestClient(app)
    finally:
        app.dependency_overrides.clear()
        engine.dispose()


def test_create_list_and_summary_are_persistent(client: TestClient):
    created = client.post("/api/v1/domain/clients", json={"name": "Atlas Bank", "client_type": "BANK"})
    assert created.status_code == 201
    client_id = created.json()["id"]

    listed = client.get("/api/v1/domain/clients")
    assert listed.status_code == 200
    assert listed.json() == [{"id": client_id, "name": "Atlas Bank", "client_type": "BANK"}]

    summary = client.get("/api/v1/domain/summary")
    assert summary.status_code == 200
    assert summary.json()["counts"]["clients"] == 1
    assert summary.json()["counts"]["audit_events"] == 1


def test_create_client_is_idempotent_by_name(client: TestClient):
    first = client.post("/api/v1/domain/clients", json={"name": "Nova Finance", "client_type": "FINANCIAL_INSTITUTION"})
    second = client.post("/api/v1/domain/clients", json={"name": "Nova Finance", "client_type": "FINANCIAL_INSTITUTION"})
    assert first.status_code == 201
    assert second.status_code == 201
    assert first.json()["id"] == second.json()["id"]
    summary = client.get("/api/v1/domain/summary").json()["counts"]
    assert summary["clients"] == 1
    assert summary["audit_events"] == 1


def _seed_product_module(tmp_path: Path, *, product_name: str = "Collections", module_name: str = "Promise-to-Pay") -> tuple[str, str]:
    from app.domain.models import Module, Product

    engine = create_engine(f"sqlite:///{tmp_path / 'api.db'}", connect_args={"check_same_thread": False})
    factory = sessionmaker(bind=engine, expire_on_commit=False)
    with factory() as session:
        product = Product(name=product_name, description="Implementation registry test product")
        session.add(product)
        session.flush()
        module = Module(product_id=product.id, name=module_name, description="Implementation registry test module")
        session.add(module)
        session.commit()
        result = (product.id, module.id)
    engine.dispose()
    return result


def test_list_catalog_and_create_implementation(client: TestClient, tmp_path: Path):
    bank = client.post("/api/v1/domain/clients", json={"name": "Crescent Bank", "client_type": "BANK"}).json()
    product_id, module_id = _seed_product_module(tmp_path)

    products = client.get("/api/v1/domain/products")
    assert products.status_code == 200
    assert products.json()[0]["id"] == product_id
    assert products.json()[0]["name"] == "Collections"

    modules = client.get(f"/api/v1/domain/modules?product_id={product_id}")
    assert modules.status_code == 200
    assert modules.json() == [{
        "id": module_id,
        "product_id": product_id,
        "name": "Promise-to-Pay",
        "description": "Implementation registry test module",
        "active": True,
    }]

    payload = {
        "client_id": bank["id"],
        "product_id": product_id,
        "module_id": module_id,
        "name": "Crescent PTP Implementation",
        "release_version": "R1",
    }
    created = client.post("/api/v1/domain/implementations", json=payload)
    assert created.status_code == 201
    body = created.json()
    assert body["client_name"] == "Crescent Bank"
    assert body["product_name"] == "Collections"
    assert body["module_name"] == "Promise-to-Pay"
    assert body["release_version"] == "R1"
    assert body["status"] == "ACTIVE"

    listed = client.get("/api/v1/domain/implementations")
    assert listed.status_code == 200
    assert listed.json() == [body]

    summary = client.get("/api/v1/domain/summary").json()["counts"]
    assert summary["implementations"] == 1
    assert summary["audit_events"] == 2  # client + implementation creation


def test_create_implementation_is_idempotent_by_client_module_release(client: TestClient, tmp_path: Path):
    bank = client.post("/api/v1/domain/clients", json={"name": "Atlas Bank", "client_type": "BANK"}).json()
    product_id, module_id = _seed_product_module(tmp_path)
    payload = {
        "client_id": bank["id"],
        "product_id": product_id,
        "module_id": module_id,
        "name": "Atlas PTP Implementation",
        "release_version": "R1",
    }
    first = client.post("/api/v1/domain/implementations", json=payload)
    second = client.post("/api/v1/domain/implementations", json=payload)
    assert first.status_code == 201
    assert second.status_code == 201
    assert first.json()["id"] == second.json()["id"]
    summary = client.get("/api/v1/domain/summary").json()["counts"]
    assert summary["implementations"] == 1
    assert summary["audit_events"] == 2


def test_create_implementation_rejects_module_product_mismatch(client: TestClient, tmp_path: Path):
    from app.domain.models import Module, Product

    bank = client.post("/api/v1/domain/clients", json={"name": "Meridian Bank", "client_type": "BANK"}).json()
    first_product_id, module_id = _seed_product_module(tmp_path)

    engine = create_engine(f"sqlite:///{tmp_path / 'api.db'}", connect_args={"check_same_thread": False})
    factory = sessionmaker(bind=engine, expire_on_commit=False)
    with factory() as session:
        other = Product(name="Loan Management")
        session.add(other)
        session.commit()
        other_id = other.id
    engine.dispose()

    response = client.post("/api/v1/domain/implementations", json={
        "client_id": bank["id"],
        "product_id": other_id,
        "module_id": module_id,
        "name": "Invalid mixed implementation",
        "release_version": "R1",
    })
    assert response.status_code == 422
    assert response.json()["detail"] == "MODULE_PRODUCT_MISMATCH"

    modules = client.get(f"/api/v1/domain/modules?product_id={first_product_id}")
    assert modules.status_code == 200
    assert len(modules.json()) == 1


def test_create_list_method_and_draft_version(client: TestClient, tmp_path: Path):
    product_id, module_id = _seed_product_module(tmp_path)

    method_response = client.post("/api/v1/domain/methods", json={
        "module_id": module_id,
        "name": "PTP Event Handling",
        "description": "Reusable Promise-to-Pay event processing method",
    })
    assert method_response.status_code == 201
    method = method_response.json()
    assert method["product_id"] == product_id
    assert method["product_name"] == "Collections"
    assert method["module_id"] == module_id
    assert method["module_name"] == "Promise-to-Pay"

    listed_methods = client.get("/api/v1/domain/methods")
    assert listed_methods.status_code == 200
    assert listed_methods.json() == [method]

    version_response = client.post("/api/v1/domain/method-versions", json={
        "method_id": method["id"],
        "version": "PTP-EVENT-v2",
        "summary": "Replay-safe processing candidate",
    })
    assert version_response.status_code == 201
    version = version_response.json()
    assert version["method_id"] == method["id"]
    assert version["method_name"] == "PTP Event Handling"
    assert version["version"] == "PTP-EVENT-v2"
    assert version["status"] == "DRAFT"
    assert version["revoked_at"] is None

    listed_versions = client.get("/api/v1/domain/method-versions")
    assert listed_versions.status_code == 200
    assert listed_versions.json() == [version]

    summary = client.get("/api/v1/domain/summary").json()["counts"]
    assert summary["methods"] == 1
    assert summary["method_versions"] == 1
    assert summary["audit_events"] == 2  # method + draft version creation


def test_method_and_version_creation_are_idempotent(client: TestClient, tmp_path: Path):
    _, module_id = _seed_product_module(tmp_path)
    payload = {"module_id": module_id, "name": "PTP Event Handling", "description": "Reusable method"}
    first_method = client.post("/api/v1/domain/methods", json=payload)
    second_method = client.post("/api/v1/domain/methods", json=payload)
    assert first_method.status_code == 201
    assert second_method.status_code == 201
    assert first_method.json()["id"] == second_method.json()["id"]

    version_payload = {"method_id": first_method.json()["id"], "version": "PTP-EVENT-v2", "summary": "Candidate"}
    first_version = client.post("/api/v1/domain/method-versions", json=version_payload)
    second_version = client.post("/api/v1/domain/method-versions", json=version_payload)
    assert first_version.status_code == 201
    assert second_version.status_code == 201
    assert first_version.json()["id"] == second_version.json()["id"]
    assert second_version.json()["status"] == "DRAFT"

    summary = client.get("/api/v1/domain/summary").json()["counts"]
    assert summary["methods"] == 1
    assert summary["method_versions"] == 1
    assert summary["audit_events"] == 2


def test_method_version_create_rejects_unknown_method(client: TestClient):
    response = client.post("/api/v1/domain/method-versions", json={
        "method_id": "missing-method-id",
        "version": "PTP-EVENT-v2",
    })
    assert response.status_code == 404
    assert response.json()["detail"] == "METHOD_NOT_FOUND"


def _seed_method_with_draft_and_authority(client: TestClient, tmp_path: Path, *, principal: str = "baseline.approver@creed.local", learning: bool = True):
    _, module_id = _seed_product_module(tmp_path)
    method = client.post("/api/v1/domain/methods", json={
        "module_id": module_id,
        "name": "PTP Event Handling",
        "description": "Reusable PTP event processing",
    }).json()
    version = client.post("/api/v1/domain/method-versions", json={
        "method_id": method["id"],
        "version": "PTP-EVENT-v1",
        "summary": "Initial baseline candidate",
    }).json()
    authority = client.post("/api/v1/domain/authorities", json={
        "principal": principal,
        "display_name": "Baseline Approver",
        "role_title": "Transformation Assurance Lead",
        "active": True,
        "can_submit_human_decision": False,
        "can_approve_learning": learning,
        "can_authorize_recall": False,
    }).json()
    return method, version, authority


def test_baseline_method_version_approval_is_human_governed(client: TestClient, tmp_path: Path):
    method, version, authority = _seed_method_with_draft_and_authority(client, tmp_path)
    response = client.post(
        f"/api/v1/domain/method-versions/{version['id']}/baseline-approval",
        json={
            "reviewer": authority["principal"],
            "reason": "Initial approved baseline for existing Promise-to-Pay implementations.",
        },
        headers={"X-CREED-Principal": authority["principal"]},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["id"] == version["id"]
    assert body["method_id"] == method["id"]
    assert body["status"] == "APPROVED"

    listed = client.get("/api/v1/domain/method-versions").json()
    assert listed[0]["status"] == "APPROVED"

    summary = client.get("/api/v1/domain/summary").json()["counts"]
    assert summary["methods"] == 1
    assert summary["method_versions"] == 1
    assert summary["human_authorities"] == 1
    assert summary["audit_events"] == 4  # method + draft + authority + baseline approval


def test_baseline_method_version_approval_fails_closed_without_permission(client: TestClient, tmp_path: Path):
    _, version, authority = _seed_method_with_draft_and_authority(
        client, tmp_path, principal="no.learning@creed.local", learning=False
    )
    missing = client.post(
        f"/api/v1/domain/method-versions/{version['id']}/baseline-approval",
        json={"reviewer": authority["principal"], "reason": "Initial baseline"},
    )
    assert missing.status_code == 403
    assert missing.json()["detail"] == "AUTHORITY_PRINCIPAL_REQUIRED"

    denied = client.post(
        f"/api/v1/domain/method-versions/{version['id']}/baseline-approval",
        json={"reviewer": authority["principal"], "reason": "Initial baseline"},
        headers={"X-CREED-Principal": authority["principal"]},
    )
    assert denied.status_code == 403
    assert denied.json()["detail"] == "LEARNING_APPROVAL_AUTHORITY_REQUIRED"


def test_baseline_method_version_approval_cannot_be_reused(client: TestClient, tmp_path: Path):
    method, version, authority = _seed_method_with_draft_and_authority(client, tmp_path)
    payload = {"reviewer": authority["principal"], "reason": "Initial governed baseline"}
    headers = {"X-CREED-Principal": authority["principal"]}
    first = client.post(f"/api/v1/domain/method-versions/{version['id']}/baseline-approval", json=payload, headers=headers)
    assert first.status_code == 200

    repeat = client.post(f"/api/v1/domain/method-versions/{version['id']}/baseline-approval", json=payload, headers=headers)
    assert repeat.status_code == 409
    assert repeat.json()["detail"] == "METHOD_VERSION_NOT_DRAFT"

    v2 = client.post("/api/v1/domain/method-versions", json={
        "method_id": method["id"],
        "version": "PTP-EVENT-v2",
        "summary": "Later candidate",
    }).json()
    second = client.post(f"/api/v1/domain/method-versions/{v2['id']}/baseline-approval", json=payload, headers=headers)
    assert second.status_code == 409
    assert second.json()["detail"] == "METHOD_BASELINE_ALREADY_ESTABLISHED"


def _seed_evidence_document(tmp_path: Path, *, title: str = "CFG-CRESCENT-PTP-01") -> str:
    from app.domain.models import EvidenceDocument

    engine = create_engine(f"sqlite:///{tmp_path / 'api.db'}", connect_args={"check_same_thread": False})
    factory = sessionmaker(bind=engine, expire_on_commit=False)
    with factory() as session:
        doc = EvidenceDocument(
            source="LOCAL_REPOSITORY",
            title=title,
            document_type="CONFIGURATION",
            version="1.0",
            content_hash=(title.lower().replace("-", "") + "0" * 64)[:64],
            original_filename=f"{title}.pdf",
            mime_type="application/pdf",
            parse_status="PARSED",
            index_status="INDEXED",
            extracted_text="Configuration evidence for implementation method usage.",
            char_count=58,
            chunk_count=1,
            metadata_json={"test": True},
        )
        session.add(doc)
        session.commit()
        result = doc.id
    engine.dispose()
    return result


def _seed_dependency_prerequisites(client: TestClient, tmp_path: Path, *, client_name: str = "Crescent Bank") -> tuple[dict, dict, str]:
    bank = client.post("/api/v1/domain/clients", json={"name": client_name, "client_type": "BANK"}).json()
    product_id, module_id = _seed_product_module(tmp_path)
    implementation = client.post("/api/v1/domain/implementations", json={
        "client_id": bank["id"],
        "product_id": product_id,
        "module_id": module_id,
        "name": f"{client_name} PTP Implementation",
        "release_version": "R1",
    }).json()
    method = client.post("/api/v1/domain/methods", json={
        "module_id": module_id,
        "name": "PTP Event Handling",
        "description": "Reusable PTP method",
    }).json()
    version = client.post("/api/v1/domain/method-versions", json={
        "method_id": method["id"],
        "version": "PTP-EVENT-v1",
        "summary": "Registered method version",
    }).json()
    evidence_id = _seed_evidence_document(tmp_path)
    return implementation, version, evidence_id


def test_register_list_and_remove_implementation_method_dependency(client: TestClient, tmp_path: Path):
    implementation, version, evidence_id = _seed_dependency_prerequisites(client, tmp_path)

    payload = {
        "implementation_id": implementation["id"],
        "method_version_id": version["id"],
        "evidence_document_id": evidence_id,
    }
    created = client.post("/api/v1/domain/dependencies", json=payload)
    assert created.status_code == 201
    body = created.json()
    assert body["relationship"] == "USES_METHOD_VERSION"
    assert body["implementation_id"] == implementation["id"]
    assert body["client_name"] == "Crescent Bank"
    assert body["method_version_id"] == version["id"]
    assert body["method_version"] == "PTP-EVENT-v1"
    assert body["evidence_document_id"] == evidence_id
    assert body["evidence_title"] == "CFG-CRESCENT-PTP-01"

    listed = client.get("/api/v1/domain/dependencies")
    assert listed.status_code == 200
    assert listed.json() == [body]

    repeated = client.post("/api/v1/domain/dependencies", json=payload)
    assert repeated.status_code == 201
    assert repeated.json()["id"] == body["id"]

    summary = client.get("/api/v1/domain/summary").json()["counts"]
    assert summary["edges"] == 1
    assert summary["audit_events"] == 5  # client + implementation + method + version + dependency

    removed = client.request(
        "DELETE",
        f"/api/v1/domain/dependencies/{body['id']}",
        json={"reason": "Implementation inventory corrected after configuration review."},
    )
    assert removed.status_code == 204
    assert client.get("/api/v1/domain/dependencies").json() == []

    summary = client.get("/api/v1/domain/summary").json()["counts"]
    assert summary["edges"] == 0
    assert summary["audit_events"] == 6


def test_dependency_requires_matching_module(client: TestClient, tmp_path: Path):
    implementation, _, evidence_id = _seed_dependency_prerequisites(client, tmp_path)

    from app.domain.models import DeliveryMethod, MethodVersion, Module, Product

    engine = create_engine(f"sqlite:///{tmp_path / 'api.db'}", connect_args={"check_same_thread": False})
    factory = sessionmaker(bind=engine, expire_on_commit=False)
    with factory() as session:
        product = Product(name="Loan Management")
        session.add(product)
        session.flush()
        module = Module(product_id=product.id, name="Repayment Schedule")
        session.add(module)
        session.flush()
        method = DeliveryMethod(module_id=module.id, name="Schedule Event Handling")
        session.add(method)
        session.flush()
        version = MethodVersion(method_id=method.id, version="SCHEDULE-v1", status="APPROVED")
        session.add(version)
        session.commit()
        other_version_id = version.id
    engine.dispose()

    response = client.post("/api/v1/domain/dependencies", json={
        "implementation_id": implementation["id"],
        "method_version_id": other_version_id,
        "evidence_document_id": evidence_id,
    })
    assert response.status_code == 422
    assert response.json()["detail"] == "IMPLEMENTATION_METHOD_MODULE_MISMATCH"


def test_dependency_does_not_silently_replace_evidence(client: TestClient, tmp_path: Path):
    implementation, version, evidence_id = _seed_dependency_prerequisites(client, tmp_path)
    first = client.post("/api/v1/domain/dependencies", json={
        "implementation_id": implementation["id"],
        "method_version_id": version["id"],
        "evidence_document_id": evidence_id,
    })
    assert first.status_code == 201

    other_evidence_id = _seed_evidence_document(tmp_path, title="REL-CRESCENT-2026-04")
    response = client.post("/api/v1/domain/dependencies", json={
        "implementation_id": implementation["id"],
        "method_version_id": version["id"],
        "evidence_document_id": other_evidence_id,
    })
    assert response.status_code == 409
    assert response.json()["detail"] == "DEPENDENCY_ALREADY_EXISTS_WITH_DIFFERENT_EVIDENCE"


def test_create_list_and_update_human_authority(client: TestClient):
    payload = {
        "principal": "qa.lead@creed.local",
        "display_name": "QA Lead",
        "role_title": "Quality Assurance Lead",
        "active": True,
        "can_submit_human_decision": True,
        "can_approve_learning": False,
        "can_authorize_recall": False,
    }
    created = client.post("/api/v1/domain/authorities", json=payload)
    assert created.status_code == 201
    body = created.json()
    assert body["principal"] == payload["principal"]
    assert body["can_submit_human_decision"] is True
    assert body["active"] is True

    listed = client.get("/api/v1/domain/authorities")
    assert listed.status_code == 200
    assert listed.json() == [body]

    updated = client.patch(f"/api/v1/domain/authorities/{body['id']}", json={
        "role_title": "Transformation Assurance Lead",
        "can_approve_learning": True,
        "can_authorize_recall": True,
    })
    assert updated.status_code == 200
    revised = updated.json()
    assert revised["principal"] == payload["principal"]
    assert revised["role_title"] == "Transformation Assurance Lead"
    assert revised["can_submit_human_decision"] is True
    assert revised["can_approve_learning"] is True
    assert revised["can_authorize_recall"] is True

    summary = client.get("/api/v1/domain/summary").json()["counts"]
    assert summary["human_authorities"] == 1
    assert summary["audit_events"] == 2  # registration + update


def test_human_authority_create_is_idempotent_only_for_same_configuration(client: TestClient):
    payload = {
        "principal": "assurance@creed.local",
        "display_name": "Assurance Lead",
        "role_title": "Assurance Lead",
        "active": True,
        "can_submit_human_decision": True,
        "can_approve_learning": True,
        "can_authorize_recall": True,
    }
    first = client.post("/api/v1/domain/authorities", json=payload)
    second = client.post("/api/v1/domain/authorities", json=payload)
    assert first.status_code == 201
    assert second.status_code == 201
    assert first.json()["id"] == second.json()["id"]

    conflict = client.post("/api/v1/domain/authorities", json={**payload, "role_title": "Different Role"})
    assert conflict.status_code == 409
    assert conflict.json()["detail"] == "AUTHORITY_PRINCIPAL_ALREADY_EXISTS"

    summary = client.get("/api/v1/domain/summary").json()["counts"]
    assert summary["human_authorities"] == 1
    assert summary["audit_events"] == 1


def test_human_authority_update_rejects_unknown_record(client: TestClient):
    response = client.patch("/api/v1/domain/authorities/missing-authority", json={"active": False})
    assert response.status_code == 404
    assert response.json()["detail"] == "AUTHORITY_NOT_FOUND"


def _seed_deployment_prerequisites(client: TestClient, tmp_path: Path) -> tuple[dict, str]:
    bank = client.post("/api/v1/domain/clients", json={"name": "Harbour Bank", "client_type": "BANK"}).json()
    product_id, module_id = _seed_product_module(tmp_path)
    implementation = client.post("/api/v1/domain/implementations", json={
        "client_id": bank["id"],
        "product_id": product_id,
        "module_id": module_id,
        "name": "Harbour PTP Implementation",
        "release_version": "R4.2",
    }).json()
    evidence_id = _seed_evidence_document(tmp_path, title="REL-HARBOUR-2026-08")
    return implementation, evidence_id


def test_record_and_list_release_deployment(client: TestClient, tmp_path: Path):
    implementation, evidence_id = _seed_deployment_prerequisites(client, tmp_path)
    payload = {
        "implementation_id": implementation["id"],
        "environment": "PRODUCTION",
        "deployed_at": "2026-08-18T03:15:00Z",
        "deployment_reference": "CHG-HB-2041",
        "evidence_document_id": evidence_id,
        "notes": "Production rollout completed after release approval.",
    }

    created = client.post("/api/v1/domain/deployments", json=payload)
    assert created.status_code == 201
    body = created.json()
    assert body["implementation_id"] == implementation["id"]
    assert body["implementation_name"] == "Harbour PTP Implementation"
    assert body["client_name"] == "Harbour Bank"
    assert body["release_version"] == "R4.2"
    assert body["environment"] == "PRODUCTION"
    assert body["status"] == "DEPLOYED"
    assert body["deployment_reference"] == "CHG-HB-2041"
    assert body["evidence_document_id"] == evidence_id
    assert body["evidence_title"] == "REL-HARBOUR-2026-08"

    listed = client.get("/api/v1/domain/deployments")
    assert listed.status_code == 200
    assert listed.json() == [body]

    repeated = client.post("/api/v1/domain/deployments", json=payload)
    assert repeated.status_code == 201
    assert repeated.json()["id"] == body["id"]

    summary = client.get("/api/v1/domain/summary").json()["counts"]
    assert summary["deployments"] == 1
    assert summary["audit_events"] == 3  # client + implementation + deployment


def test_deployment_does_not_silently_replace_same_event(client: TestClient, tmp_path: Path):
    implementation, evidence_id = _seed_deployment_prerequisites(client, tmp_path)
    base = {
        "implementation_id": implementation["id"],
        "environment": "UAT",
        "deployed_at": "2026-08-17T10:30:00Z",
        "deployment_reference": "REL-HB-UAT-17",
        "evidence_document_id": evidence_id,
        "notes": "UAT release evidence.",
    }
    first = client.post("/api/v1/domain/deployments", json=base)
    assert first.status_code == 201

    other_evidence_id = _seed_evidence_document(tmp_path, title="REL-HARBOUR-2026-08-ALT")
    conflicting = client.post("/api/v1/domain/deployments", json={
        **base,
        "evidence_document_id": other_evidence_id,
    })
    assert conflicting.status_code == 409
    assert conflicting.json()["detail"] == "DEPLOYMENT_EVENT_ALREADY_EXISTS"


def test_deployment_validates_environment_and_prerequisites(client: TestClient, tmp_path: Path):
    implementation, evidence_id = _seed_deployment_prerequisites(client, tmp_path)
    invalid_environment = client.post("/api/v1/domain/deployments", json={
        "implementation_id": implementation["id"],
        "environment": "MOON",
        "deployed_at": "2026-08-18T03:15:00Z",
        "evidence_document_id": evidence_id,
    })
    assert invalid_environment.status_code == 422

    missing_impl = client.post("/api/v1/domain/deployments", json={
        "implementation_id": "missing-implementation",
        "environment": "SIT",
        "deployed_at": "2026-08-18T03:15:00Z",
        "evidence_document_id": evidence_id,
    })
    assert missing_impl.status_code == 404
    assert missing_impl.json()["detail"] == "IMPLEMENTATION_NOT_FOUND"

    missing_evidence = client.post("/api/v1/domain/deployments", json={
        "implementation_id": implementation["id"],
        "environment": "SIT",
        "deployed_at": "2026-08-18T03:15:00Z",
        "evidence_document_id": "missing-evidence",
    })
    assert missing_evidence.status_code == 404
    assert missing_evidence.json()["detail"] == "EVIDENCE_DOCUMENT_NOT_FOUND"


def _seed_responsibility_authority(client: TestClient, *, principal: str, name: str, active: bool = True) -> dict:
    response = client.post("/api/v1/domain/authorities", json={
        "principal": principal,
        "display_name": name,
        "role_title": "Delivery Assurance",
        "active": active,
        "can_submit_human_decision": False,
        "can_approve_learning": False,
        "can_authorize_recall": False,
    })
    assert response.status_code == 201
    return response.json()


def test_create_list_reassign_and_remove_responsibility(client: TestClient, tmp_path: Path):
    product_id, module_id = _seed_product_module(tmp_path)
    first = _seed_responsibility_authority(client, principal="owner.one@creed.local", name="Owner One")
    second = _seed_responsibility_authority(client, principal="owner.two@creed.local", name="Owner Two")

    created = client.post("/api/v1/domain/ownership", json={
        "scope_type": "MODULE",
        "scope_id": module_id,
        "responsibility_type": "MODULE_OWNER",
        "authority_id": first["id"],
        "team_name": "Collections Delivery",
    })
    assert created.status_code == 201
    body = created.json()
    assert body["scope_name"] == "Promise-to-Pay"
    assert body["scope_context"] == "Collections / Promise-to-Pay"
    assert body["responsibility_type"] == "MODULE_OWNER"
    assert body["principal"] == "owner.one@creed.local"
    assert body["team_name"] == "Collections Delivery"

    listed = client.get("/api/v1/domain/ownership")
    assert listed.status_code == 200
    assert listed.json() == [body]

    updated = client.patch(f"/api/v1/domain/ownership/{body['id']}", json={
        "authority_id": second["id"],
        "team_name": "Collections Engineering",
        "reason": "Primary module ownership transferred after operating-model update.",
    })
    assert updated.status_code == 200
    revised = updated.json()
    assert revised["principal"] == "owner.two@creed.local"
    assert revised["team_name"] == "Collections Engineering"

    summary = client.get("/api/v1/domain/summary").json()["counts"]
    assert summary["responsibilities"] == 1
    assert summary["audit_events"] == 4  # two authorities + assignment + reassignment

    removed = client.request(
        "DELETE",
        f"/api/v1/domain/ownership/{body['id']}",
        json={"reason": "Ownership scope retired after module consolidation."},
    )
    assert removed.status_code == 204
    assert client.get("/api/v1/domain/ownership").json() == []
    summary = client.get("/api/v1/domain/summary").json()["counts"]
    assert summary["responsibilities"] == 0
    assert summary["audit_events"] == 5


def test_responsibility_assignment_is_idempotent_but_does_not_silently_replace_owner(client: TestClient, tmp_path: Path):
    product_id, _ = _seed_product_module(tmp_path)
    first = _seed_responsibility_authority(client, principal="product.owner@creed.local", name="Product Owner")
    second = _seed_responsibility_authority(client, principal="other.owner@creed.local", name="Other Owner")
    payload = {
        "scope_type": "PRODUCT",
        "scope_id": product_id,
        "responsibility_type": "PRODUCT_OWNER",
        "authority_id": first["id"],
        "team_name": "Collections Product",
    }
    one = client.post("/api/v1/domain/ownership", json=payload)
    two = client.post("/api/v1/domain/ownership", json=payload)
    assert one.status_code == 201
    assert two.status_code == 201
    assert one.json()["id"] == two.json()["id"]

    conflict = client.post("/api/v1/domain/ownership", json={**payload, "authority_id": second["id"]})
    assert conflict.status_code == 409
    assert conflict.json()["detail"] == "RESPONSIBILITY_ALREADY_ASSIGNED"


def test_responsibility_validates_scope_role_and_active_authority(client: TestClient, tmp_path: Path):
    _, module_id = _seed_product_module(tmp_path)
    inactive = _seed_responsibility_authority(
        client, principal="inactive.owner@creed.local", name="Inactive Owner", active=False
    )
    inactive_response = client.post("/api/v1/domain/ownership", json={
        "scope_type": "MODULE",
        "scope_id": module_id,
        "responsibility_type": "MODULE_OWNER",
        "authority_id": inactive["id"],
    })
    assert inactive_response.status_code == 422
    assert inactive_response.json()["detail"] == "AUTHORITY_INACTIVE"

    active = _seed_responsibility_authority(client, principal="qa.owner@creed.local", name="QA Owner")
    bad_role = client.post("/api/v1/domain/ownership", json={
        "scope_type": "MODULE",
        "scope_id": module_id,
        "responsibility_type": "IMPLEMENTATION_LEAD",
        "authority_id": active["id"],
    })
    assert bad_role.status_code == 422
    assert bad_role.json()["detail"] == "RESPONSIBILITY_ROLE_NOT_ALLOWED_FOR_SCOPE"

    missing_scope = client.post("/api/v1/domain/ownership", json={
        "scope_type": "MODULE",
        "scope_id": "missing-module",
        "responsibility_type": "QA_OWNER",
        "authority_id": active["id"],
    })
    assert missing_scope.status_code == 404
    assert missing_scope.json()["detail"] == "RESPONSIBILITY_SCOPE_NOT_FOUND"


def test_product_registry_create_list_update_and_duplicate_protection(client: TestClient):
    payload = {
        "name": "Collections",
        "description": "Collections platform for repayment and recovery workflows.",
        "active": True,
    }
    created = client.post("/api/v1/domain/products", json=payload)
    assert created.status_code == 201
    product = created.json()
    assert product["name"] == "Collections"
    assert product["description"] == payload["description"]
    assert product["active"] is True

    repeated = client.post("/api/v1/domain/products", json=payload)
    assert repeated.status_code == 201
    assert repeated.json()["id"] == product["id"]

    conflict = client.post("/api/v1/domain/products", json={
        **payload,
        "description": "A different definition that must not silently replace the catalog record.",
    })
    assert conflict.status_code == 409
    assert conflict.json()["detail"] == "PRODUCT_NAME_ALREADY_EXISTS"

    listed = client.get("/api/v1/domain/products")
    assert listed.status_code == 200
    assert listed.json() == [product]

    deactivated = client.patch(f"/api/v1/domain/products/{product['id']}", json={"active": False})
    assert deactivated.status_code == 200
    assert deactivated.json()["active"] is False
    assert deactivated.json()["name"] == "Collections"

    summary = client.get("/api/v1/domain/summary").json()["counts"]
    assert summary["products"] == 1
    assert summary["audit_events"] == 2  # PRODUCT_CREATED + PRODUCT_UPDATED


def test_product_registry_rejects_blank_names_and_missing_product_update(client: TestClient):
    blank = client.post("/api/v1/domain/products", json={"name": "  ", "active": True})
    assert blank.status_code == 422

    missing = client.patch("/api/v1/domain/products/00000000-0000-4000-8000-000000000000", json={"active": False})
    assert missing.status_code == 404
    assert missing.json()["detail"] == "PRODUCT_NOT_FOUND"


def test_module_registry_create_list_update_and_duplicate_protection(client: TestClient):
    product_response = client.post("/api/v1/domain/products", json={
        "name": "Collections",
        "description": "Collections product",
        "active": True,
    })
    assert product_response.status_code == 201
    product = product_response.json()

    payload = {
        "product_id": product["id"],
        "name": "Promise-to-Pay",
        "description": "Promise-to-Pay lifecycle and event processing.",
        "active": True,
    }
    created = client.post("/api/v1/domain/modules", json=payload)
    assert created.status_code == 201
    module = created.json()
    assert module["product_id"] == product["id"]
    assert module["name"] == "Promise-to-Pay"
    assert module["description"] == payload["description"]
    assert module["active"] is True

    repeated = client.post("/api/v1/domain/modules", json=payload)
    assert repeated.status_code == 201
    assert repeated.json()["id"] == module["id"]

    conflict = client.post("/api/v1/domain/modules", json={
        **payload,
        "description": "A conflicting module definition that must not silently replace the catalog record.",
    })
    assert conflict.status_code == 409
    assert conflict.json()["detail"] == "MODULE_NAME_ALREADY_EXISTS"

    listed = client.get(f"/api/v1/domain/modules?product_id={product['id']}")
    assert listed.status_code == 200
    assert listed.json() == [module]

    deactivated = client.patch(f"/api/v1/domain/modules/{module['id']}", json={"active": False})
    assert deactivated.status_code == 200
    assert deactivated.json()["active"] is False
    assert deactivated.json()["name"] == "Promise-to-Pay"

    summary = client.get("/api/v1/domain/summary").json()["counts"]
    assert summary["modules"] == 1
    assert summary["audit_events"] == 3  # PRODUCT_CREATED + MODULE_CREATED + MODULE_UPDATED


def test_module_registry_requires_active_product_and_valid_input(client: TestClient):
    inactive_product = client.post("/api/v1/domain/products", json={
        "name": "Dormant Platform",
        "description": "Inactive catalog product",
        "active": False,
    }).json()

    blocked = client.post("/api/v1/domain/modules", json={
        "product_id": inactive_product["id"],
        "name": "Legacy Module",
        "active": True,
    })
    assert blocked.status_code == 422
    assert blocked.json()["detail"] == "PRODUCT_INACTIVE"

    missing_product = client.post("/api/v1/domain/modules", json={
        "product_id": "00000000-0000-4000-8000-000000000000",
        "name": "Unknown Product Module",
        "active": True,
    })
    assert missing_product.status_code == 404
    assert missing_product.json()["detail"] == "PRODUCT_NOT_FOUND"

    blank = client.post("/api/v1/domain/modules", json={
        "product_id": inactive_product["id"],
        "name": "  ",
        "active": True,
    })
    assert blank.status_code == 422

    missing = client.patch("/api/v1/domain/modules/00000000-0000-4000-8000-000000000000", json={"active": False})
    assert missing.status_code == 404
    assert missing.json()["detail"] == "MODULE_NOT_FOUND"
