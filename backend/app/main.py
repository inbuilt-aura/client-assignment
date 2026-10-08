from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import router
from app.core.config import settings

app = FastAPI(title="NOVA Vendor Service Area API", version="0.1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "PATCH", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization"],
)
app.include_router(router, prefix="/v1")


@app.get("/health")
def health():
    return {"status": "ok"}
