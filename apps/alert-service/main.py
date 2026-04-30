from fastapi import FastAPI
import uvicorn
from app.api.alert_routes import router


app = FastAPI(
    title="Alert Service",
)

app.include_router(router)


@app.get("/")
def root():
    return {
        "service": "alert-service",
        "status": "running",
    }

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
    )