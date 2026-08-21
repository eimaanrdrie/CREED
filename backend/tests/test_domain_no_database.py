from fastapi.testclient import TestClient

from app.main import app
import app.api.domain as domain_api


def test_domain_endpoint_fails_cleanly_without_database():
    def broken_db():
        raise RuntimeError("DATABASE_NOT_CONFIGURED")
        yield

    original = domain_api.get_db
    domain_api.get_db = broken_db
    response = TestClient(app).get("/api/v1/domain/summary")
    try:
        assert response.status_code == 503
        assert response.json()["detail"] == "DATABASE_NOT_CONFIGURED"
    finally:
        domain_api.get_db = original
