import random

from fastapi import APIRouter


router = APIRouter(
    prefix="/risk",
    tags=["Risk"],
)


@router.post("/score")
def score(
    file_id: str,
    owner_id: str,
):
    risk = random.randint(0, 100)

    label = (
        "HIGH"
        if risk >= 80
        else "LOW"
    )

    status = (
        "QUARANTINED"
        if risk >= 80
        else "ACTIVE"
    )

    return {
        "file_id": file_id,
        "risk_score": risk,
        "label": label,
        "status": status,
    }