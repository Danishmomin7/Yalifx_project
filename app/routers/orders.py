import secrets
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from .. import models
from ..database import get_db
from ..schemas import CheckoutRequest, OrderPublic
from ..services import calculate_commission, calculate_total, order_to_dict


router = APIRouter(prefix="/api/orders", tags=["orders"])


@router.get("/downloads/{download_token}/{slug}")
def download_order_asset(download_token: str, slug: str, db: Session = Depends(get_db)):
    order = db.query(models.Order).filter(models.Order.download_token == download_token).first()
    if not order:
        raise HTTPException(status_code=404, detail="Download link is invalid")

    item = (
        db.query(models.OrderItem)
        .join(models.Asset, models.OrderItem.asset_id == models.Asset.id)
        .filter(models.OrderItem.order_id == order.id, models.Asset.slug == slug)
        .first()
    )
    if not item or not item.asset.gdrive_source_link:
        raise HTTPException(status_code=404, detail="Asset download is not available")

    return RedirectResponse(item.asset.gdrive_source_link, status_code=307)


@router.post("", response_model=OrderPublic, status_code=status.HTTP_201_CREATED)
def create_order(payload: CheckoutRequest, db: Session = Depends(get_db)) -> dict[str, Any]:
    normalized_email = payload.buyer_email.strip().lower()
    if "@" not in normalized_email or "." not in normalized_email.split("@")[-1]:
        raise HTTPException(status_code=422, detail="Valid buyer email is required")

    line_items: list[tuple[models.Asset, int]] = []
    line_totals: list[int] = []
    for requested in payload.items:
        asset = db.query(models.Asset).filter(models.Asset.slug == requested.slug).first()
        if not asset:
            raise HTTPException(status_code=404, detail=f"Asset not found: {requested.slug}")
        line_items.append((asset, requested.quantity))
        line_totals.append(asset.price_cents * requested.quantity)

    total_cents = calculate_total(line_totals, payload.plan)
    commission_cents = calculate_commission(total_cents)
    order = models.Order(
        buyer_email=normalized_email,
        buyer_studio=payload.buyer_studio,
        plan=payload.plan,
        total_cents=total_cents,
        commission_cents=commission_cents,
        download_token=secrets.token_urlsafe(18),
    )
    db.add(order)
    db.flush()

    for asset, quantity in line_items:
        asset.sales_count += quantity
        db.add(
            models.OrderItem(
                order=order,
                asset=asset,
                quantity=quantity,
                unit_price_cents=asset.price_cents,
            )
        )

    db.commit()
    db.refresh(order)
    return order_to_dict(order)

