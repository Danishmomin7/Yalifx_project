from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_search_endpoint_returns_assets_for_query():
    response = client.get("/api/search", params={"q": "smoke"})

    assert response.status_code == 200
    payload = response.json()
    assert isinstance(payload, list)
    assert len(payload) >= 1
    assert all("title" in asset for asset in payload)
