from fastapi.testclient import TestClient


def test_health_check(client: TestClient):
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["service"] == "DriveScope Control Plane"


def test_models_list(client: TestClient):
    response = client.get("/api/v1/models")
    assert response.status_code == 200
    models = response.json()
    assert len(models) >= 2
    adapter_ids = [m["adapter_id"] for m in models]
    assert "mock-vla-v1" in adapter_ids
