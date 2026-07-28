import asyncio
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware

from app.core.config import get_settings
from app.middleware.request_context import RequestContextMiddleware, obter_ip_cliente
from app.routers import (
    auth,
    motoristas,
    ocorrencias,
    pedidos,
    romaneios,
    transportadoras,
    usuarios,
    veiculos,
    webhooks_tms,
)
from app.services.uno_sync_scheduler import sincronizar_uno_periodicamente

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    sync_task = asyncio.create_task(sincronizar_uno_periodicamente())
    try:
        yield
    finally:
        sync_task.cancel()


app = FastAPI(title="KAMI CO. — Romaneios", version="0.1.0", lifespan=lifespan)

# Rate limiting (governança: 100 req/min por IP). key_func usa o IP real (atrás do nginx,
# request.client.host seria o IP do proxy, não do cliente).
limiter = Limiter(key_func=obter_ip_cliente, default_limits=[f"{settings.rate_limit_por_minuto}/minute"])
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_middleware(SlowAPIMiddleware)

app.add_middleware(RequestContextMiddleware)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_allowed_origins_lista,
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
app.include_router(usuarios.router, prefix="/api")


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}
