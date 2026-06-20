from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from .. import models
from ..database import get_db
from ..schemas import EnterpriseInquiryCreate, EnterpriseInquiryPublic


router = APIRouter(tags=["business"])


@router.get("/api/plans")
def list_plans():
    return [
        {
            "id": "single_purchase",
            "name": "Single Purchase",
            "price_cents": 0,
            "benefit": "Per-asset licensing",
        },
        {
            "id": "studio_monthly",
            "name": "Studio Monthly",
            "price_cents": 9900,
            "benefit": "15% marketplace discount and shared team billing",
        },
        {
            "id": "studio_annual",
            "name": "Studio Annual",
            "price_cents": 99000,
            "benefit": "15% marketplace discount, priority review, and invoice support",
        },
        {
            "id": "enterprise",
            "name": "Enterprise",
            "price_cents": None,
            "benefit": "Custom licensing for game and film studios",
        },
    ]


@router.post(
    "/api/enterprise/inquiries",
    response_model=EnterpriseInquiryPublic,
    status_code=status.HTTP_201_CREATED,
)
def create_enterprise_inquiry(payload: EnterpriseInquiryCreate, db: Session = Depends(get_db)):
    inquiry = models.EnterpriseInquiry(**payload.model_dump())
    db.add(inquiry)
    db.commit()
    db.refresh(inquiry)
    return {
        "id": inquiry.id,
        "contact_name": inquiry.contact_name,
        "email": inquiry.email,
        "company": inquiry.company,
        "use_case": inquiry.use_case,
        "seats": inquiry.seats,
        "message": inquiry.message,
    }

