from fastapi import FastAPI
import uvicorn

from app.api.risk_routes import router as risk_router

app = FastAPI(title="risk-service")

app.include_router(risk_router)


@app.get("/")
def root():
    return {
        "service": "risk-service",
        "status": "healthy"
    }


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )