from pydantic import BaseModel, Field


class CreatorPublic(BaseModel):
    id: int
    name: str
    studio_type: str
    location: str
    bio: str
    rating: float


class AssetPublic(BaseModel):
    id: int
    title: str
    slug: str
    description: str
    category: str
    format: str
    engine: str
    license_type: str
    price_cents: int
    preview_url: str
    gdrive_preview_link: str | None
    gdrive_source_link: str | None
    file_size_mb: int
    version: str
    frames: int
    resolution: str
    curated: bool
    featured: bool
    tags: list[str]
    sales_count: int
    rating: float
    creator: CreatorPublic


class AssetCreate(BaseModel):
    title: str = Field(..., min_length=3, max_length=140)
    description: str = Field(..., min_length=20, max_length=1200)
    category: str = Field(..., min_length=2, max_length=80)
    format: str = Field(..., min_length=2, max_length=80)
    engine: str = Field(..., min_length=2, max_length=80)
    license_type: str = Field(default="Standard", min_length=2, max_length=80)
    price_cents: int = Field(..., ge=0, le=250000)
    file_size_mb: int = Field(default=512, ge=1, le=50000)
    version: str = Field(default="1.0", max_length=40)
    frames: int = Field(default=120, ge=1, le=10000)
    resolution: str = Field(default="512 voxel", max_length=40)
    tags: list[str] = Field(default_factory=list, max_length=12)
    creator_name: str = Field(..., min_length=2, max_length=120)
    creator_type: str = Field(default="Freelance FX Artist", max_length=80)
    creator_location: str = Field(default="Remote", max_length=120)
    preview_url: str | None = Field(default=None, max_length=240)
    gdrive_preview_link: str | None = Field(default=None, max_length=500)
    gdrive_source_link: str | None = Field(default=None, max_length=500)


class CheckoutItem(BaseModel):
    slug: str = Field(..., min_length=2)
    quantity: int = Field(default=1, ge=1, le=20)


class CheckoutRequest(BaseModel):
    buyer_email: str = Field(..., min_length=5, max_length=180)
    buyer_studio: str = Field(default="Independent Studio", min_length=2, max_length=160)
    plan: str = Field(default="single_purchase", max_length=80)
    items: list[CheckoutItem] = Field(..., min_length=1, max_length=20)


class OrderLinePublic(BaseModel):
    asset_slug: str
    asset_title: str
    quantity: int
    unit_price_cents: int
    download_url: str


class OrderPublic(BaseModel):
    id: int
    buyer_email: str
    buyer_studio: str
    plan: str
    total_cents: int
    commission_cents: int
    status: str
    download_token: str
    items: list[OrderLinePublic]


class EnterpriseInquiryCreate(BaseModel):
    contact_name: str = Field(..., min_length=2, max_length=140)
    email: str = Field(..., min_length=5, max_length=180)
    company: str = Field(..., min_length=2, max_length=180)
    use_case: str = Field(..., min_length=2, max_length=80)
    seats: int = Field(default=5, ge=1, le=10000)
    message: str = Field(default="", max_length=1200)


class EnterpriseInquiryPublic(BaseModel):
    id: int
    contact_name: str
    email: str
    company: str
    use_case: str
    seats: int
    message: str

