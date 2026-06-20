from datetime import UTC, datetime

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .database import Base


def utc_now() -> datetime:
    return datetime.now(UTC)


class Creator(Base):
    __tablename__ = "creators"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(120), nullable=False, unique=True, index=True)
    studio_type: Mapped[str] = mapped_column(String(80), nullable=False, default="Freelance FX Artist")
    location: Mapped[str] = mapped_column(String(120), nullable=False, default="Remote")
    bio: Mapped[str] = mapped_column(Text, nullable=False, default="")
    rating: Mapped[float] = mapped_column(Float, nullable=False, default=4.8)
    payout_rate: Mapped[float] = mapped_column(Float, nullable=False, default=0.8)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utc_now)

    assets = relationship("Asset", back_populates="creator", cascade="all, delete-orphan")


class Asset(Base):
    __tablename__ = "assets"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    title: Mapped[str] = mapped_column(String(140), nullable=False, index=True)
    slug: Mapped[str] = mapped_column(String(160), nullable=False, unique=True, index=True)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    category: Mapped[str] = mapped_column(String(80), nullable=False, index=True)
    format: Mapped[str] = mapped_column(String(80), nullable=False, index=True)
    engine: Mapped[str] = mapped_column(String(80), nullable=False, index=True)
    license_type: Mapped[str] = mapped_column(String(80), nullable=False, default="Standard")
    price_cents: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    preview_url: Mapped[str] = mapped_column(String(240), nullable=False, default="/static/media/community-upload.png")
    file_size_mb: Mapped[int] = mapped_column(Integer, nullable=False, default=512)
    version: Mapped[str] = mapped_column(String(40), nullable=False, default="1.0")
    frames: Mapped[int] = mapped_column(Integer, nullable=False, default=120)
    resolution: Mapped[str] = mapped_column(String(40), nullable=False, default="512 voxel")
    curated: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, index=True)
    featured: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, index=True)
    tags_text: Mapped[str] = mapped_column(Text, nullable=False, default="[]")
    sales_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    rating: Mapped[float] = mapped_column(Float, nullable=False, default=4.7)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utc_now)

    creator_id: Mapped[int] = mapped_column(Integer, ForeignKey("creators.id"), nullable=False, index=True)
    creator = relationship("Creator", back_populates="assets")
    order_items = relationship("OrderItem", back_populates="asset")


class Order(Base):
    __tablename__ = "orders"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    buyer_email: Mapped[str] = mapped_column(String(180), nullable=False, index=True)
    buyer_studio: Mapped[str] = mapped_column(String(160), nullable=False, default="Independent Studio")
    plan: Mapped[str] = mapped_column(String(80), nullable=False, default="single_purchase")
    total_cents: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    commission_cents: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    download_token: Mapped[str] = mapped_column(String(80), nullable=False, unique=True, index=True)
    status: Mapped[str] = mapped_column(String(40), nullable=False, default="paid")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utc_now)

    items = relationship("OrderItem", back_populates="order", cascade="all, delete-orphan")


class OrderItem(Base):
    __tablename__ = "order_items"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    order_id: Mapped[int] = mapped_column(Integer, ForeignKey("orders.id"), nullable=False, index=True)
    asset_id: Mapped[int] = mapped_column(Integer, ForeignKey("assets.id"), nullable=False, index=True)
    quantity: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    unit_price_cents: Mapped[int] = mapped_column(Integer, nullable=False)

    order = relationship("Order", back_populates="items")
    asset = relationship("Asset", back_populates="order_items")


class EnterpriseInquiry(Base):
    __tablename__ = "enterprise_inquiries"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    contact_name: Mapped[str] = mapped_column(String(140), nullable=False)
    email: Mapped[str] = mapped_column(String(180), nullable=False, index=True)
    company: Mapped[str] = mapped_column(String(180), nullable=False)
    use_case: Mapped[str] = mapped_column(String(80), nullable=False)
    seats: Mapped[int] = mapped_column(Integer, nullable=False, default=5)
    message: Mapped[str] = mapped_column(Text, nullable=False, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utc_now)
