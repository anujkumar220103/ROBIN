# Tests for health check endpoints.

def test_root_endpoint(client):
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "ROBIN AI"
    assert "version" in data
    assert "message" in data


def test_health_endpoint(client):
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["service"] == "ROBIN AI"
    assert "version" in data


def test_health_does_not_require_database(client):
    """The /health endpoint must not depend on database availability."""
    response = client.get("/api/v1/health")
    assert response.status_code == 200


def test_database_health_returns_valid_shape(client):
    """DB health check returns healthy or unhealthy — both shapes are valid."""
    response = client.get("/api/v1/health/db")
    assert response.status_code in (200, 503)
    data = response.json()
    assert "status" in data
    assert "database" in data
    assert data["database"] in ("connected", "disconnected")


def test_unknown_route_returns_404(client):
    response = client.get("/api/v1/does-not-exist")
    assert response.status_code == 404
