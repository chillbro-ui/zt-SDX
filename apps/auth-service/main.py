from fastapi import FastAPI
import uvicorn

from app.core.config import settings

app = FastAPI(title="auth-service")


@app.get("/")
def root():
    return {
        "service": "auth-service",
        "status": "healthy"
    }


@app.get("/health")
def health():
    return {
        "service": "auth-service",
        "env": settings.ENVIRONMENT,
        "postgres": {
            "host": settings.POSTGRES_HOST,
            "port": settings.POSTGRES_PORT,
            "db": settings.POSTGRES_DB
        },
        "redis": {
            "host": settings.REDIS_HOST,
            "port": settings.REDIS_PORT
        },
        "jwt_loaded": bool(settings.JWT_SECRET)
    }


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )