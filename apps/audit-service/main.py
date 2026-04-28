from fastapi import FastAPI
import uvicorn

from app.api.audit_routes import router as audit_router

app = FastAPI(title="audit-service")

app.include_router(audit_router)

@app.get("/")
def root():
    return {
        "service": "audit-service",
        "status": "healthy"
    }


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )