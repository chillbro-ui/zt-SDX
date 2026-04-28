from fastapi import FastAPI
import uvicorn
from app.api.file_routes import router as file_router

app = FastAPI(title="file-service")
app.include_router(file_router)

@app.get("/")
def root():
    return {
        "service": "file-service",
        "status": "healthy"
    }


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )