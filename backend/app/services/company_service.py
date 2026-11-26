# Handles company profile retrieval and update operations.

from sqlalchemy.orm import Session

from app.models.company import Company


def get_company_by_id(db: Session, company_id) -> Company | None:
    return db.query(Company).filter(Company.id == company_id).first()


def update_company_name(db: Session, company: Company, new_name: str) -> Company:
    """Update only the company display name. Slug stays stable after registration."""
    company.name = new_name.strip()
    db.commit()
    db.refresh(company)
    return company
