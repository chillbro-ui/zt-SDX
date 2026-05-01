import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
import uvicorn

from app.api import score, risk, alerts, train
from app.core.config import settings
from app.core.db import engine, Base

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info(f"Starting risk-service [{settings.ENVIRONMENT}]")

    # Import ALL models so SQLAlchemy registers them before create_all
    from app.models.risk_profile import RiskProfile  # noqa: F401
    from app.models.risk_event import RiskEvent       # noqa: F401
    from app.models.risk_feature import RiskFeature   # noqa: F401
    from app.models.alert import Alert                # noqa: F401

    Base.metadata.create_all(bind=engine)
    logger.info("Database tables ready")

    # Try to load the latest ML model from MinIO on startup
    try:
        from app.core.db import SessionLocal
        from app.training.trainer import ModelTrainer
        db = SessionLocal()
        ModelTrainer(db).load_latest()
        db.close()
    except Exception as exc:
        logger.warning(f"Could not load ML model on startup (will use rules only): {exc}")

    yield

    logger.info("Shutting down risk-service")


app = FastAPI(
    title="risk-service",
    description="ML-powered security risk scoring engine",
    version="1.0.0",
    lifespan=lifespan,
)

# All routers share the /risk prefix defined inside each router module
app.include_router(score.router)
app.include_router(risk.router)
app.include_router(alerts.router)
app.include_router(train.router)


@app.get("/", tags=["meta"])
def root():
    return {"service": "risk-service", "status": "healthy"}


@app.get("/health", tags=["meta"])
def health():
    return {
        "service": "risk-service",
        "env": settings.ENVIRONMENT,
        "postgres": {
            "host": settings.POSTGRES_HOST,
            "port": settings.POSTGRES_PORT,
            "db": settings.POSTGRES_DB,
        },
        "redis": {
            "host": settings.REDIS_HOST,
            "port": settings.REDIS_PORT,
        },
        "minio": {
            "host": settings.MINIO_HOST,
            "port": settings.MINIO_PORT,
            "bucket": settings.MINIO_BUCKET,
        },
        "jwt_loaded": bool(settings.JWT_SECRET),
        "scoring": {
            "rule_weight": settings.RULE_WEIGHT,
            "ml_weight": settings.ML_WEIGHT,
        },
    }


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
    )
