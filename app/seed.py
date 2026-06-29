from typing import Any

from sqlalchemy.orm import Session

from . import models
from .services import clean_tags, slugify, unique_slug


CREATOR_DATA: list[dict[str, Any]] = [
    {
        "name": "YaliFX Curated",
        "studio_type": "YaliFX Quality Desk",
        "location": "Global",
        "bio": "Internal benchmark assets for cinematic and realtime production standards.",
        "rating": 4.95,
    },
    {
        "name": "Aarav Volumes",
        "studio_type": "Freelance FX Artist",
        "location": "Mumbai, India",
        "bio": "Houdini smoke, pyro, and dust elements for indie games and film shots.",
        "rating": 4.88,
    },
    {
        "name": "Realtime Ember Lab",
        "studio_type": "Realtime FX Studio",
        "location": "Remote",
        "bio": "Niagara and VFX Graph packs tuned for responsive gameplay and virtual production.",
        "rating": 4.82,
    },
]


ASSET_DATA: list[dict[str, Any]] = [
    {
        "title": "Hero Smoke Column VDB",
        "description": "High-resolution hero smoke column with layered density, soft turbulence, and clean alpha falloff for compositing or Houdini relighting.",
        "category": "Smoke",
        "format": "VDB",
        "engine": "Houdini",
        "license_type": "Commercial",
        "price_cents": 7900,
        "preview_url": "/static/media/smoke-column.png",
        "file_size_mb": 1450,
        "frames": 180,
        "resolution": "768 voxel",
        "curated": True,
        "featured": True,
        "tags": ["vdb", "smoke", "cinematic", "compositing"],
        "sales_count": 126,
        "rating": 4.9,
        "creator": "YaliFX Curated",
    },
    {
        "title": "Pyroclastic Blast VDB",
        "description": "Dense explosive blast with rolling fire core, smoke breakup, and production-ready caches for cinematic destruction shots.",
        "category": "Explosion",
        "format": "VDB",
        "engine": "Houdini",
        "license_type": "Commercial",
        "price_cents": 12900,
        "preview_url": "/static/media/pyro-blast.png",
        "file_size_mb": 3100,
        "frames": 140,
        "resolution": "1024 voxel",
        "curated": True,
        "featured": True,
        "tags": ["explosion", "pyro", "vdb", "film"],
        "sales_count": 98,
        "rating": 4.92,
        "creator": "YaliFX Curated",
    },
    {
        "title": "Niagara Ember Sparks Pack",
        "description": "Optimized Unreal Niagara sparks with color curves, collision options, LOD settings, and modular emitters for gameplay moments.",
        "category": "Fire",
        "format": "Unreal Niagara",
        "engine": "Unreal Engine",
        "license_type": "Studio",
        "price_cents": 4900,
        "preview_url": "/static/media/niagara-sparks.png",
        "file_size_mb": 220,
        "frames": 90,
        "resolution": "Realtime",
        "curated": False,
        "featured": True,
        "tags": ["unreal", "niagara", "sparks", "game"],
        "sales_count": 214,
        "rating": 4.81,
        "creator": "Realtime Ember Lab",
    },
    {
        "title": "Cumulus Cloud Bank VDB",
        "description": "Tileable cloud bank volume with soft billowing detail for matte painting, sky replacement, aerial shots, and volumetric lighting.",
        "category": "Clouds",
        "format": "VDB",
        "engine": "Blender",
        "license_type": "Commercial",
        "price_cents": 6900,
        "preview_url": "/static/media/cloud-bank.png",
        "file_size_mb": 1800,
        "frames": 1,
        "resolution": "896 voxel",
        "curated": True,
        "featured": False,
        "tags": ["cloud", "vdb", "sky", "volume"],
        "sales_count": 73,
        "rating": 4.78,
        "creator": "Aarav Volumes",
    },
    {
        "title": "Unity Arcane Ribbons",
        "description": "Unity VFX Graph ribbon system with editable gradients, spawn masks, and motion-friendly trails for magic attacks and AR effects.",
        "category": "Magic",
        "format": "Unity VFX Graph",
        "engine": "Unity",
        "license_type": "Studio",
        "price_cents": 5400,
        "preview_url": "/static/media/arcane-ribbons.png",
        "file_size_mb": 180,
        "frames": 120,
        "resolution": "Realtime",
        "curated": False,
        "featured": True,
        "tags": ["unity", "vfx graph", "magic", "ar"],
        "sales_count": 167,
        "rating": 4.76,
        "creator": "Realtime Ember Lab",
    },
    {
        "title": "Ground Dust Hit Cache",
        "description": "Practical ground-impact dust cache with secondary wisps and debris-friendly timing for footfalls, crashes, and vehicle shots.",
        "category": "Dust",
        "format": "Alembic Cache",
        "engine": "Cinema 4D",
        "license_type": "Commercial",
        "price_cents": 3900,
        "preview_url": "/static/media/dust-hit.png",
        "file_size_mb": 760,
        "frames": 96,
        "resolution": "Mesh cache",
        "curated": False,
        "featured": False,
        "tags": ["dust", "impact", "alembic", "motion graphics"],
        "sales_count": 112,
        "rating": 4.68,
        "creator": "Aarav Volumes",
    },
    {
        "title": "Plasma Shockwave HDA",
        "description": "Procedural Houdini digital asset for circular energy shockwaves, with art-directable rings, turbulence, and export presets.",
        "category": "Energy",
        "format": "Houdini HDA",
        "engine": "Houdini",
        "license_type": "Commercial",
        "price_cents": 8900,
        "preview_url": "/static/media/plasma-shockwave.png",
        "file_size_mb": 340,
        "frames": 160,
        "resolution": "Procedural",
        "curated": True,
        "featured": False,
        "tags": ["hda", "energy", "procedural", "shockwave"],
        "sales_count": 61,
        "rating": 4.86,
        "creator": "YaliFX Curated",
    },
    {
        "title": "Low-Lying Fog Loop",
        "description": "Looping realtime fog layer with gentle drift, depth fade, and adjustable density for horror levels, forests, and virtual sets.",
        "category": "Fog",
        "format": "Unreal Niagara",
        "engine": "Unreal Engine",
        "license_type": "Standard",
        "price_cents": 2900,
        "preview_url": "/static/media/fog-loop.png",
        "file_size_mb": 95,
        "frames": 240,
        "resolution": "Realtime",
        "curated": False,
        "featured": False,
        "tags": ["fog", "unreal", "loop", "environment"],
        "sales_count": 188,
        "rating": 4.72,
        "creator": "Aarav Volumes",
    },
]


def seed_db(db: Session) -> None:
    if db.query(models.Asset).first():
        return

    creators: dict[str, models.Creator] = {}
    for item in CREATOR_DATA:
        creator = models.Creator(**item)
        db.add(creator)
        creators[creator.name] = creator

    db.flush()

    for item in ASSET_DATA:
        asset_data: dict[str, Any] = dict(item)
        creator_name: str = asset_data.pop("creator")
        tags: list[str] = asset_data.pop("tags")
        base_slug = slugify(asset_data["title"])
        slug = unique_slug(db, asset_data["title"])
        while db.query(models.Asset).filter(models.Asset.slug == slug).first():
            slug = f"{base_slug}-{len(db.query(models.Asset).all()) + 1}"
        asset = models.Asset(
            **asset_data,
            slug=slug,
            tags_text=clean_tags(tags),
            creator=creators[creator_name],
        )
        db.add(asset)

    db.commit()

