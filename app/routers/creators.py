from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from .. import models
from ..database import get_db
from ..schemas import CreatorPublic
from ..services import creator_dashboard


router = APIRouter(prefix="/api/creators", tags=["creators"])


@router.get("", response_model=list[CreatorPublic])
def list_creators(db: Session = Depends(get_db)) -> list[dict[str, Any]]:
    creators = db.query(models.Creator).order_by(models.Creator.rating.desc()).all()
    return [
        {
            "id": creator.id,
            "name": creator.name,
            "studio_type": creator.studio_type,
            "location": creator.location,
            "bio": creator.bio,
            "rating": creator.rating,
        }
        for creator in creators
    ]


@router.get("/{creator_id}/dashboard")
def get_creator_dashboard(creator_id: int, db: Session = Depends(get_db)) -> dict[str, Any]:
    creator = db.query(models.Creator).filter(models.Creator.id == creator_id).first()
    if not creator:
        raise HTTPException(status_code=404, detail="Creator not found")
    return creator_dashboard(creator)

