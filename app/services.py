import json
import re
import secrets
from collections import Counter
from decimal import Decimal, ROUND_HALF_UP
from typing import Any, cast

from fastapi import HTTPException
from sqlalchemy.orm import Session

from . import models


ALLOWED_CATEGORIES = {
    "Smoke",
    "Fire",
    "Explosion",
    "Clouds",
    "Magic",
    "Dust",
    "Energy",
    "Fog",
}

ALLOWED_FORMATS = {
    "VDB",
    "Unreal Niagara",
    "Unity VFX Graph",
    "Alembic Cache",
    "Houdini HDA",
}

ALLOWED_ENGINES = {
    "Houdini",
    "Unreal Engine",
    "Unity",
    "Blender",
    "Cinema 4D",
}

COMMISSION_RATE = Decimal("0.20")
SUBSCRIPTION_DISCOUNT = Decimal("0.15")


def parse_tags(tags_text: str) -> list[str]:
    try:
        tags = json.loads(tags_text or "[]")
    except json.JSONDecodeError:
        return []
    if not isinstance(tags, list):
        return []
    tags = cast(list[Any], tags)
    return [str(tag) for tag in tags][:12]


def clean_tags(tags: list[str]) -> str:
    cleaned: list[str] = []
    for tag in tags:
        value = re.sub(r"\s+", " ", tag.strip().lower())
        if value and value not in cleaned:
            cleaned.append(value)
    return json.dumps(cleaned[:12])


def slugify(value: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    return slug or secrets.token_hex(4)


def unique_slug(db: Session, title: str) -> str:
    base = slugify(title)
    slug = base
    counter = 2
    while db.query(models.Asset).filter(models.Asset.slug == slug).first():
        slug = f"{base}-{counter}"
        counter += 1
    return slug


def validate_catalog_values(category: str, format_name: str, engine: str) -> None:
    if category not in ALLOWED_CATEGORIES:
        raise HTTPException(status_code=422, detail=f"Unsupported category: {category}")
    if format_name not in ALLOWED_FORMATS:
        raise HTTPException(status_code=422, detail=f"Unsupported format: {format_name}")
    if engine not in ALLOWED_ENGINES:
        raise HTTPException(status_code=422, detail=f"Unsupported engine: {engine}")


def asset_to_dict(asset: models.Asset) -> dict[str, Any]:
    return {
        "id": asset.id,
        "title": asset.title,
        "slug": asset.slug,
        "description": asset.description,
        "category": asset.category,
        "format": asset.format,
        "engine": asset.engine,
        "license_type": asset.license_type,
        "price_cents": asset.price_cents,
        "preview_url": asset.preview_url,
        "gdrive_preview_link": asset.gdrive_preview_link,
        "gdrive_source_link": asset.gdrive_source_link,
        "file_size_mb": asset.file_size_mb,
        "version": asset.version,
        "frames": asset.frames,
        "resolution": asset.resolution,
        "curated": asset.curated,
        "featured": asset.featured,
        "tags": parse_tags(asset.tags_text),
        "sales_count": asset.sales_count,
        "rating": asset.rating,
        "creator": {
            "id": asset.creator.id,
            "name": asset.creator.name,
            "studio_type": asset.creator.studio_type,
            "location": asset.creator.location,
            "bio": asset.creator.bio,
            "rating": asset.creator.rating,
        },
    }


def order_to_dict(order: models.Order) -> dict[str, Any]:
    return {
        "id": order.id,
        "buyer_email": order.buyer_email,
        "buyer_studio": order.buyer_studio,
        "plan": order.plan,
        "total_cents": order.total_cents,
        "commission_cents": order.commission_cents,
        "status": order.status,
        "download_token": order.download_token,
        "items": [
            {
                "asset_slug": item.asset.slug,
                "asset_title": item.asset.title,
                "quantity": item.quantity,
                "unit_price_cents": item.unit_price_cents,
                "download_url": f"/downloads/{order.download_token}/{item.asset.slug}",
            }
            for item in order.items
        ],
    }


def calculate_total(line_totals: list[int], plan: str) -> int:
    subtotal = sum(line_totals)
    if plan in {"studio_monthly", "studio_annual"}:
        discounted = Decimal(subtotal) * (Decimal("1") - SUBSCRIPTION_DISCOUNT)
        return int(discounted.quantize(Decimal("1"), rounding=ROUND_HALF_UP))
    return subtotal


def calculate_commission(total_cents: int) -> int:
    commission = Decimal(total_cents) * COMMISSION_RATE
    return int(commission.quantize(Decimal("1"), rounding=ROUND_HALF_UP))


def creator_dashboard(creator: models.Creator) -> dict[str, Any]:
    assets = list(creator.assets)
    revenue_cents = 0
    units_sold = 0
    category_counter: Counter[str] = Counter()

    for asset in assets:
        units_sold += asset.sales_count
        revenue_cents += int(asset.sales_count * asset.price_cents * creator.payout_rate)
        category_counter[asset.category] += 1

    return {
        "creator": {
            "id": creator.id,
            "name": creator.name,
            "studio_type": creator.studio_type,
            "location": creator.location,
            "rating": creator.rating,
        },
        "asset_count": len(assets),
        "units_sold": units_sold,
        "estimated_payout_cents": revenue_cents,
        "top_categories": category_counter.most_common(4),
        "assets": [
            {
                "title": asset.title,
                "slug": asset.slug,
                "price_cents": asset.price_cents,
                "sales_count": asset.sales_count,
                "curated": asset.curated,
            }
            for asset in sorted(assets, key=lambda item: item.sales_count, reverse=True)
        ],
    }

