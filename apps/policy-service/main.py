from fastapi import FastAPI
import uvicorn

from app.api.policy_routes import router as policy_router

app = FastAPI(title="policy-service")


app.include_router(policy_router)


@app.get("/")
def root():
    return {
        "service": "policy-service",
        "status": "healthy"
    }


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )