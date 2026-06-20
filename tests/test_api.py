import os
from pathlib import Path
from typing import Any, cast

import pytest
from fastapi.testclient import TestClient
from httpx import Response


TEST_DB = Path(__file__).resolve().parent / "test_yalifx.db"
os.environ["DATABASE_URL"] = f"sqlite:///{TEST_DB.as_posix()}"

from app.main import app  # noqa: E402
from app.database import engine  # noqa: E402


@pytest.fixture(scope="module")
def client():
    if TEST_DB.exists():
        TEST_DB.unlink()
    with TestClient(app) as test_client:
        yield test_client
    engine.dispose()
    if TEST_DB.exists():
        TEST_DB.unlink(missing_ok=True)


def test_health(client: TestClient) -> None:
    response: Response = cast(Response, client.get("/api/health"))  # type: ignore[reportUnknownMemberType]
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_marketplace_page_renders(client: TestClient) -> None:
    response: Response = cast(Response, client.get("/"))  # type: ignore[reportUnknownMemberType]
    assert response.status_code == 200
    assert "YaliFX Marketplace" in response.text


def test_seeded_assets_can_be_filtered(client: TestClient) -> None:
    response: Response = cast(Response, client.get("/api/assets", params={"format": "VDB", "curated": True}))  # type: ignore[reportUnknownMemberType]
    assert response.status_code == 200
    assets: Any = response.json()
    assert assets
    assert all(asset["format"] == "VDB" for asset in assets)
    assert all(asset["curated"] for asset in assets)


def test_create_asset(client: TestClient) -> None:
    payload: dict[str, Any] = {
        "title": "Realtime Portal Wisps",
        "description": "Looping realtime portal wisps with soft noise, clean masks, and adjustable color controls for games.",
        "category": "Magic",
        "format": "Unity VFX Graph",
        "engine": "Unity",
        "price_cents": 4500,
        "creator_name": "Test Creator",
        "tags": ["unity", "magic"],
    }
    response: Response = cast(Response, client.post("/api/assets", json=payload))  # type: ignore[reportUnknownMemberType]
    assert response.status_code == 201
    body: Any = response.json()
    assert body["slug"] == "realtime-portal-wisps"
    assert body["curated"] is False


def test_checkout_calculates_commission(client: TestClient) -> None:
    response: Response = cast(Response, client.post(  # type: ignore[reportUnknownMemberType]
        "/api/orders",
        json={
            "buyer_email": "buyer@example.com",
            "buyer_studio": "Example Studio",
            "plan": "single_purchase",
            "items": [{"slug": "hero-smoke-column-vdb", "quantity": 1}],
        },
    ))
    assert response.status_code == 201
    order: Any = response.json()
    assert order["total_cents"] == 7900
    assert order["commission_cents"] == 1580
    assert order["items"][0]["download_url"].startswith("/downloads/")


def test_enterprise_inquiry(client: TestClient) -> None:
    response: Response = cast(Response, client.post(  # type: ignore[reportUnknownMemberType]
        "/api/enterprise/inquiries",
        json={
            "contact_name": "Nisha Producer",
            "email": "nisha@example.com",
            "company": "Indie Volume Works",
            "use_case": "Virtual Production",
            "seats": 18,
            "message": "Need enterprise licensing for a realtime stage.",
        },
    ))
    assert response.status_code == 201
    assert response.json()["company"] == "Indie Volume Works"
