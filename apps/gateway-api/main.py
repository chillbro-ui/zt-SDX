import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

from app.api.gateway_routes import router as gateway_router

app = FastAPI(title="gateway-api")

# ─── CORS ─────────────────────────────────────────────────────────────────────
# Origins are read from the CORS_ORIGINS env var (comma-separated).
# When the frontend team delivers their app, add its origin to .env:
#   CORS_ORIGINS=http://localhost:5173,https://your-prod-domain.com
#
# Falls back to localhost:5173 (Vite default) for local dev.

_raw = os.getenv("CORS_ORIGINS", "http://localhost:5173")
ALLOWED_ORIGINS = [o.strip() for o in _raw.split(",") if o.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─── Routes ───────────────────────────────────────────────────────────────────

app.include_router(gateway_router)


@app.get("/")
def root():
    return {
        "service": "gateway-api",
        "status": "healthy",
        "cors_origins": ALLOWED_ORIGINS,
    }


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
    )
