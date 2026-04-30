from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.services.org_service import (
    create_department,
    create_org,
    get_org,
    list_departments,
    list_orgs,
)

router = APIRouter(prefix="/orgs", tags=["organizations"])


@router.post("/")
def create_organization(
    name: str,
    domain: str,
    legal_name: Optional[str] = None,
    industry: Optional[str] = None,
    country: str = "IN",
    size: Optional[int] = None,
    db: Session = Depends(get_db),
):
    org = create_org(
        db=db,
        name=name,
        domain=domain,
        legal_name=legal_name,
        industry=industry,
        country=country,
        size=size,
    )
    return {
        "id": str(org.id),
        "name": org.name,
        "domain": org.domain,
        "country": org.country,
        "created_at": org.created_at.isoformat() if org.created_at else None,
        "message": "Organization created with default departments.",
    }


@router.get("/")
def get_organizations(db: Session = Depends(get_db)):
    orgs = list_orgs(db)
    return [
        {
            "id": str(o.id),
            "name": o.name,
            "domain": o.domain,
            "industry": o.industry,
            "country": o.country,
            "created_at": o.created_at.isoformat() if o.created_at else None,
        }
        for o in orgs
    ]


@router.get("/{org_id}")
def get_organization(org_id: str, db: Session = Depends(get_db)):
    org = get_org(db, org_id)
    if not org:
        raise HTTPException(status_code=404, detail="Organization not found")
    return {
        "id": str(org.id),
        "name": org.name,
        "legal_name": org.legal_name,
        "domain": org.domain,
        "industry": org.industry,
        "country": org.country,
        "size": org.size,
        "created_at": org.created_at.isoformat() if org.created_at else None,
    }


@router.get("/{org_id}/departments")
def get_departments(org_id: str, db: Session = Depends(get_db)):
    org = get_org(db, org_id)
    if not org:
        raise HTTPException(status_code=404, detail="Organization not found")
    depts = list_departments(db, org_id)
    return [
        {
            "id": str(d.id),
            "name": d.name,
            "org_id": str(d.org_id),
            "created_at": d.created_at.isoformat() if d.created_at else None,
        }
        for d in depts
    ]


@router.post("/{org_id}/departments")
def add_department(org_id: str, name: str, db: Session = Depends(get_db)):
    org = get_org(db, org_id)
    if not org:
        raise HTTPException(status_code=404, detail="Organization not found")
    dept = create_department(db, org_id, name)
    return {
        "id": str(dept.id),
        "name": dept.name,
        "org_id": str(dept.org_id),
    }
