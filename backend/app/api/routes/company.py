# Company profile endpoints — view and update the authenticated user's company.

from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from app.api.dependencies import (
    get_current_company,
    get_current_user,
    require_company_admin,
    verify_csrf_token,
)
from app.db.session import get_db
from app.models.company import Company
from app.models.user import User
from app.schemas.company import CompanyResponse, CompanyUpdateRequest
from app.services.company_service import update_company_name

router = APIRouter(prefix="/company", tags=["Company"])


@router.get("/me", response_model=CompanyResponse)
def get_my_company(
    current_company: Company = Depends(get_current_company),
):
    """Return the company associated with the authenticated user.

    Company ID authenticated user se milti hai — URL parameter se nahi.
    """
    return current_company


@router.patch("/me", response_model=CompanyResponse)
def update_my_company(
    data: CompanyUpdateRequest,
    request: Request,
    _csrf: None = Depends(verify_csrf_token),
    current_user: User = Depends(require_company_admin),
    current_company: Company = Depends(get_current_company),
    db: Session = Depends(get_db),
):
    """Update the company display name. Only company admins can do this.

    Company ID, slug, ownership, aur role modify nahi ho sakti.
    """
    return update_company_name(db, current_company, data.name)
