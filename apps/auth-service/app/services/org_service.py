from typing import Optional

from sqlalchemy.orm import Session

from app.models.department import Department
from app.models.organization import Organization

DEFAULT_DEPARTMENTS = ["Engineering", "Finance", "HR", "Security", "Legal", "Operations"]


def create_org(
    db: Session,
    name: str,
    domain: str,
    legal_name: Optional[str] = None,
    industry: Optional[str] = None,
    country: str = "IN",
    size: Optional[int] = None,
):
    org = Organization(
        name=name,
        domain=domain,
        legal_name=legal_name,
        industry=industry,
        country=country,
        size=size,
    )
    db.add(org)
    db.commit()
    db.refresh(org)

    # Auto-create default departments
    for dept_name in DEFAULT_DEPARTMENTS:
        dept = Department(org_id=org.id, name=dept_name)
        db.add(dept)
    db.commit()

    return org


def get_org(db: Session, org_id: str):
    return db.query(Organization).filter(Organization.id == org_id).first()


def get_org_by_domain(db: Session, domain: str):
    return db.query(Organization).filter(Organization.domain == domain).first()


def list_orgs(db: Session):
    return db.query(Organization).all()


def list_departments(db: Session, org_id: str):
    return db.query(Department).filter(Department.org_id == org_id).all()


def create_department(db: Session, org_id: str, name: str):
    dept = Department(org_id=org_id, name=name)
    db.add(dept)
    db.commit()
    db.refresh(dept)
    return dept
