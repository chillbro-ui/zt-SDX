import logging

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.security.deps import get_current_user
from app.training.trainer import ModelTrainer

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/risk", tags=["training"])


class TrainResponse(BaseModel):
    status: str
    detail: dict


@router.post("/train", response_model=TrainResponse)
async def trigger_training(
    _caller: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Manually trigger a model retrain.

    Pulls latest feature history from Postgres, trains a new IsolationForest
    model, saves it to MinIO, and hot-reloads it into the live scoring engine.

    Called by: ops team, scheduled jobs
    Auth: Bearer JWT required
    """
    try:
        trainer = ModelTrainer(db)
        result = trainer.train()
    except Exception as exc:
        logger.error(f"trigger_training failed: {exc}", exc_info=True)
        raise HTTPException(status_code=500, detail="Model training failed")

    return TrainResponse(
        status=result["status"],
        detail=result,
    )
