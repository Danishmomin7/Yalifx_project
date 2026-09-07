from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, or_
from sqlalchemy.orm import Session

from .. import models
from ..database import get_db
from ..schemas import AssetPublic
from ..services import asset_to_dict


router = APIRouter(tags=["search"])


@router.get("/api/search", response_model=list[AssetPublic])
def search_assets(
    q: str = Query(..., min_length=1, max_length=120),
    limit: int = Query(default=12, ge=1, le=50),
    db: Session = Depends(get_db),
):
    term = f"%{q.strip().lower()}%"
    query = (
        db.query(models.Asset)
        .join(models.Creator)
        .filter(
            or_(
                func.lower(models.Asset.title).like(term),
                func.lower(models.Asset.description).like(term),
                func.lower(models.Asset.tags_text).like(term),
                func.lower(models.Creator.name).like(term),
            )
        )
        .order_by(models.Asset.featured.desc(), models.Asset.curated.desc(), models.Asset.sales_count.desc())
    )

    matches = query.limit(limit).all()
    if not matches:
        raise HTTPException(status_code=404, detail="No matching Google Drive assets found")

    return [asset_to_dict(asset) for asset in matches]
