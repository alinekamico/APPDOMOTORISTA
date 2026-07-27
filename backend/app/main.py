from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.core.config import get_settings
from app.routers import auth, motoristas, ocorrencias, pedidos, romaneios, transportadoras, veiculos, webhooks_tms

settings = get_settings()

app = FastAPI(title="KAMI CO. — Romaneios", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:3002"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

Path(settings.upload_dir).mkdir(parents=True, exist_ok=True)
app.mount("/api/uploads", StaticFiles(directory=settings.upload_dir), name="uploads")

app.include_router(auth.router, prefix="/api")
app.include_router(transportadoras.router, prefix="/api")
app.include_router(veiculos.router, prefix="/api")
app.include_router(motoristas.router, prefix="/api")
app.include_router(romaneios.router, prefix="/api")
app.include_router(pedidos.router, prefix="/api")
app.include_router(ocorrencias.router, prefix="/api")
app.include_router(webhooks_tms.router, prefix="/api")


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}
