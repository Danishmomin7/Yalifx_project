import json
import re
import shutil
from pathlib import Path
from uuid import uuid4

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile, status
from fastapi.responses import RedirectResponse
from sqlalchemy import func, or_
from sqlalchemy.orm import Session

from .. import models
from ..database import get_db
from ..schemas import AssetCreate, AssetPublic
from ..services import (
    asset_to_dict,
    clean_tags,
    unique_slug,
    validate_catalog_values,
)


router = APIRouter(prefix="/api/assets", tags=["assets"])
MEDIA_DIR = Path(__file__).resolve().parents[1] / "static" / "media"


def convert_gdrive_preview(url: str | None) -> str | None:
    """Converts a standard Drive link to an iframe-friendly preview link."""
    if not url:
        return None

    match = re.search(r"/d/([a-zA-Z0-9_-]+)", url)
    if not match:
        match = re.search(r"[?&]id=([a-zA-Z0-9_-]+)", url)
    if match:
        return f"https://drive.google.com/file/d/{match.group(1)}/preview"

    return url


def convert_gdrive_source(url: str | None) -> str | None:
    """Converts a standard Drive link to a direct download link."""
    if not url:
        return None

    match = re.search(r"/d/([a-zA-Z0-9_-]+)", url)
    if not match:
        match = re.search(r"[?&]id=([a-zA-Z0-9_-]+)", url)
    if match:
        return f"https://drive.google.com/uc?export=download&id={match.group(1)}"

    return url


def save_upload(upload: UploadFile, allowed_extensions: set[str]) -> str:
    extension = Path(upload.filename or "").suffix.lower()
    if extension not in allowed_extensions:
        allowed = ", ".join(sorted(allowed_extensions))
        raise HTTPException(status_code=422, detail=f"Unsupported file type. Use: {allowed}")

    MEDIA_DIR.mkdir(parents=True, exist_ok=True)
    filename = f"{uuid4().hex}{extension}"
    target = MEDIA_DIR / filename
    with target.open("wb") as destination:
        shutil.copyfileobj(upload.file, destination)
    return f"/static/media/{filename}"


@router.get("", response_model=list[AssetPublic])
def list_assets(
    q: str | None = Query(default=None, max_length=120),
    category: str | None = Query(default=None, max_length=80),
    format: str | None = Query(default=None, max_length=80),
    engine: str | None = Query(default=None, max_length=80),
    curated: bool | None = None,
    max_price_cents: int | None = Query(default=None, ge=0),
    sort: str = Query(default="featured", pattern="^(featured|price_asc|price_desc|newest|popular|rating)$"),
    db: Session = Depends(get_db),
):
    query = db.query(models.Asset).join(models.Creator)

    if q:
        term = f"%{q.lower()}%"
        query = query.filter(
            or_(
                func.lower(models.Asset.title).like(term),
                func.lower(models.Asset.description).like(term),
                func.lower(models.Asset.tags_text).like(term),
                func.lower(models.Creator.name).like(term),
            )
        )
    if category:
        query = query.filter(models.Asset.category == category)
    if format:
        query = query.filter(models.Asset.format == format)
    if engine:
        query = query.filter(models.Asset.engine == engine)
    if curated is not None:
        query = query.filter(models.Asset.curated == curated)
    if max_price_cents is not None:
        query = query.filter(models.Asset.price_cents <= max_price_cents)

    if sort == "price_asc":
        query = query.order_by(models.Asset.price_cents.asc())
    elif sort == "price_desc":
        query = query.order_by(models.Asset.price_cents.desc())
    elif sort == "newest":
        query = query.order_by(models.Asset.created_at.desc())
    elif sort == "popular":
        query = query.order_by(models.Asset.sales_count.desc())
    elif sort == "rating":
        query = query.order_by(models.Asset.rating.desc())
    else:
        query = query.order_by(models.Asset.featured.desc(), models.Asset.curated.desc(), models.Asset.sales_count.desc())

    return [asset_to_dict(asset) for asset in query.all()]


@router.post("/upload", response_model=AssetPublic, status_code=status.HTTP_201_CREATED)
def create_uploaded_asset(
    title: str = Form(...),
    creator_name: str = Form(...),
    category: str = Form(...),
    format: str = Form(...),
    engine: str = Form(...),
    price_cents: int = Form(...),
    description: str = Form(...),
    tags: str = Form("[]"),
    creator_type: str = Form("Freelance FX Artist"),
    creator_location: str = Form("Remote"),
    preview_file: UploadFile = File(...),
    source_file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    validate_catalog_values(category, format, engine)
    if price_cents < 0 or price_cents > 250000:
        raise HTTPException(status_code=422, detail="Price must be between 0 and 250000 cents")

    try:
        parsed_tags = json.loads(tags)
    except json.JSONDecodeError:
        parsed_tags = []
    if not isinstance(parsed_tags, list):
        parsed_tags = []

    creator = (
        db.query(models.Creator)
        .filter(func.lower(models.Creator.name) == creator_name.lower())
        .first()
    )
    if not creator:
        creator = models.Creator(
            name=creator_name,
            studio_type=creator_type,
            location=creator_location,
            bio="Community creator on YaliFX.",
        )
        db.add(creator)
        db.flush()

    preview_url = save_upload(preview_file, {".mov", ".mp4"})
    source_url = save_upload(source_file, {".vdb", ".zip"})
    asset = models.Asset(
        title=title,
        slug=unique_slug(db, title),
        description=description,
        category=category,
        format=format,
        engine=engine,
        license_type="Standard",
        price_cents=price_cents,
        preview_url=preview_url,
        gdrive_source_link=source_url,
        file_size_mb=512,
        version="1.0",
        frames=120,
        resolution="512 voxel",
        curated=False,
        featured=False,
        tags_text=clean_tags([str(tag) for tag in parsed_tags]),
        creator=creator,
    )
    db.add(asset)
    db.commit()
    db.refresh(asset)
    return asset_to_dict(asset)


@router.get("/{slug}", response_model=AssetPublic)
def get_asset(slug: str, db: Session = Depends(get_db)):
    asset = db.query(models.Asset).filter(models.Asset.slug == slug).first()
    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found")
    return asset_to_dict(asset)


@router.get("/{slug}/preview")
def preview_asset(slug: str, db: Session = Depends(get_db)):
    asset = db.query(models.Asset).filter(models.Asset.slug == slug).first()
    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found")

    target = asset.gdrive_preview_link or asset.preview_url
    return RedirectResponse(target, status_code=307)


@router.get("/{slug}/download")
def download_asset(slug: str, db: Session = Depends(get_db)):
    asset = db.query(models.Asset).filter(models.Asset.slug == slug).first()
    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found")
    if not asset.gdrive_source_link:
        raise HTTPException(status_code=404, detail="Asset download is not available")

    return RedirectResponse(asset.gdrive_source_link, status_code=307)


@router.post("", response_model=AssetPublic, status_code=status.HTTP_201_CREATED)
def create_asset(payload: AssetCreate, db: Session = Depends(get_db)):
    validate_catalog_values(payload.category, payload.format, payload.engine)

    creator = (
        db.query(models.Creator)
        .filter(func.lower(models.Creator.name) == payload.creator_name.lower())
        .first()
    )
    if not creator:
        creator = models.Creator(
            name=payload.creator_name,
            studio_type=payload.creator_type,
            location=payload.creator_location,
            bio="Community creator on YaliFX.",
        )
        db.add(creator)
        db.flush()

    asset = models.Asset(
        title=payload.title,
        slug=unique_slug(db, payload.title),
        description=payload.description,
        category=payload.category,
        format=payload.format,
        engine=payload.engine,
        license_type=payload.license_type,
        price_cents=payload.price_cents,
        preview_url=payload.preview_url or "/static/media/community-upload.png",
        gdrive_preview_link=convert_gdrive_preview(payload.gdrive_preview_link),
        gdrive_source_link=convert_gdrive_source(payload.gdrive_source_link),
        file_size_mb=payload.file_size_mb,
        version=payload.version,
        frames=payload.frames,
        resolution=payload.resolution,
        curated=False,
        featured=False,
        tags_text=clean_tags(payload.tags),
        creator=creator,
    )
    db.add(asset)
    db.commit()
    db.refresh(asset)
    return asset_to_dict(asset)
