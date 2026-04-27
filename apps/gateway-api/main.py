from fastapi import FastAPI
import uvicorn

app = FastAPI(title="gateway-api")


@app.get("/")
def root():
    return {
        "service": "gateway-api",
        "status": "healthy"
    }


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )