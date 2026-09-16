def test_health(client):
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"
    assert resp.json()["service"] == "tech-genius-api"


def test_health_database(client):
    resp = client.get("/health/database")
    assert resp.status_code == 200
