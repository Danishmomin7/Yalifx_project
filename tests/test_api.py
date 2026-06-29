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


def test_seed_db_assigns_unique_slugs_for_duplicate_titles(monkeypatch: pytest.MonkeyPatch) -> None:
    from app import models
    from app import seed as seed_module
    from app.database import SessionLocal

    creator_data: list[dict[str, Any]] = [{"name": "Seed Creator", "studio_type": "Test", "location": "Remote", "bio": "", "rating": 4.8}]
    asset_data: list[dict[str, Any]] = [
            {
                "title": "Duplicate Title",
                "description": "First duplicate asset",
                "category": "Smoke",
                "format": "VDB",
                "engine": "Houdini",
                "license_type": "Commercial",
                "price_cents": 1000,
                "preview_url": "/static/media/community-upload.png",
                "file_size_mb": 10,
                "frames": 1,
                "resolution": "1 voxel",
                "curated": False,
                "featured": False,
                "tags": ["first"],
                "sales_count": 0,
                "rating": 4.7,
                "creator": "Seed Creator",
            },
            {
                "title": "Duplicate Title",
                "description": "Second duplicate asset",
                "category": "Fire",
                "format": "VDB",
                "engine": "Houdini",
                "license_type": "Commercial",
                "price_cents": 1500,
                "preview_url": "/static/media/community-upload.png",
                "file_size_mb": 12,
                "frames": 2,
                "resolution": "2 voxel",
                "curated": False,
                "featured": False,
                "tags": ["second"],
                "sales_count": 0,
                "rating": 4.8,
                "creator": "Seed Creator",
            },
        ]

    monkeypatch.setattr(seed_module, "CREATOR_DATA", creator_data)
    monkeypatch.setattr(seed_module, "ASSET_DATA", asset_data)

    db = SessionLocal()
    try:
        db.query(models.OrderItem).delete(synchronize_session=False)
        db.query(models.Order).delete(synchronize_session=False)
        db.query(models.Asset).delete(synchronize_session=False)
        db.query(models.Creator).delete(synchronize_session=False)
        db.commit()

        seed_module.seed_db(db)
        db.expire_all()
        slugs = [asset.slug for asset in db.query(models.Asset).all()]
        assert len(slugs) == len(set(slugs))
    finally:
        db.close()
