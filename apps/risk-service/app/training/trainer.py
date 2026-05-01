import io
import pickle
import logging

import numpy as np
import boto3
from sklearn.ensemble import IsolationForest
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.risk_feature import RiskFeature
from app.scoring.ml_model import ml_model, FEATURE_ORDER

logger = logging.getLogger(__name__)

MODEL_KEY = "models/isolation_forest.pkl"
MIN_SAMPLES = 100   # don't bother training until we have enough data


def _get_minio_client():
    return boto3.client(
        "s3",
        endpoint_url=f"http://{settings.MINIO_HOST}:{settings.MINIO_PORT}",
        aws_access_key_id=settings.MINIO_ROOT_USER,
        aws_secret_access_key=settings.MINIO_ROOT_PASSWORD,
    )


class ModelTrainer:
    """
    Pulls historical feature vectors from Postgres,
    trains an IsolationForest model,
    saves it to MinIO,
    then hot-reloads it into the in-process ml_model singleton.

    IsolationForest is unsupervised — it learns what "normal" looks like
    from the bulk of your data, then flags outliers. No labels needed.
    """

    def __init__(self, db: Session):
        self.db = db
        self.minio = _get_minio_client()

    def train(self) -> dict:
        """
        Full retrain cycle. Returns a status dict.
        """
        # 1. Pull feature history from Postgres
        rows = self.db.query(RiskFeature).order_by(RiskFeature.created_at.desc()).all()

        if len(rows) < MIN_SAMPLES:
            logger.warning(f"Not enough data to train ({len(rows)} rows, need {MIN_SAMPLES})")
            return {
                "status": "skipped",
                "reason": f"need {MIN_SAMPLES} samples, have {len(rows)}"
            }

        # 2. Build feature matrix (n_samples × n_features)
        X = np.array([
            [getattr(row, f) for f in FEATURE_ORDER]
            for row in rows
        ], dtype=float)

        logger.info(f"Training IsolationForest on {X.shape[0]} samples...")

        # 3. Train
        # contamination=0.05 means we expect ~5% of data to be anomalous
        model = IsolationForest(
            n_estimators=100,
            contamination=0.05,
            random_state=42,
            n_jobs=-1,
        )
        model.fit(X)

        # 4. Serialise and upload to MinIO
        model_bytes = pickle.dumps(model)
        self.minio.put_object(
            Bucket=settings.MINIO_BUCKET,
            Key=MODEL_KEY,
            Body=io.BytesIO(model_bytes),
            ContentLength=len(model_bytes),
        )
        logger.info(f"Model saved to MinIO: {settings.MINIO_BUCKET}/{MODEL_KEY}")

        # 5. Hot-reload into the live ml_model singleton (no restart needed)
        ml_model.load(model_bytes)

        return {
            "status": "success",
            "samples_used": X.shape[0],
            "model_key": MODEL_KEY,
        }

    def load_latest(self):
        """
        Called at service startup — loads the most recently trained model from MinIO
        so we don't start blind after a restart.
        """
        try:
            obj = self.minio.get_object(Bucket=settings.MINIO_BUCKET, Key=MODEL_KEY)
            model_bytes = obj["Body"].read()
            ml_model.load(model_bytes)
            logger.info("Loaded existing ML model from MinIO on startup")
        except Exception as e:
            logger.warning(f"No existing model in MinIO (will use rules only): {e}")
