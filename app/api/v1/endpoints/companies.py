from fastapi import APIRouter, Query
from uuid import UUID

from app.core.dependencies import DB, CurrentUser
from app.core.exceptions import not_found
from app.models.company import Company
from app.schemas.company import CompanyResponse
from app.schemas.common import PaginatedResponse

router = APIRouter(prefix="/companies", tags=["Companies"])


@router.get("", response_model=PaginatedResponse[CompanyResponse])
def list_companies(db: DB, page: int = Query(1, ge=1), page_size: int = Query(20, ge=1, le=100)):
    query = db.query(Company).order_by(Company.created_at.desc())
    total = query.count()
    total_pages = (total + page_size - 1) // page_size
    items = query.offset((page - 1) * page_size).limit(page_size).all()
    return PaginatedResponse[CompanyResponse](
        items=[CompanyResponse.model_validate(c) for c in items],
        page=page, page_size=page_size, total=total, total_pages=total_pages,
    )


@router.get("/{company_id}", response_model=CompanyResponse)
def get_company(company_id: UUID, db: DB):
    company = db.query(Company).filter(Company.id == company_id).first()
    if not company:
        raise not_found("COMPANY_NOT_FOUND", "Company not found")
    return CompanyResponse.model_validate(company)
