"""Aplicación FastAPI principal de VOCES.

Configura middleware de seguridad (sesiones firmadas, hosts confiables),
monta archivos estáticos, registra los routers públicos y de administración,
y siembra datos de demostración al arrancar.
"""

from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware
from starlette.middleware.trustedhost import TrustedHostMiddleware

from app.config import settings
from app.database import init_db, SessionLocal
from app.dependencies import templates
from app.services.rate_limit import rate_limiter


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    db = SessionLocal()
    try:
        from app.routers.seed import seed_demo_data

        seed_demo_data(db)
    finally:
        db.close()
    yield


app = FastAPI(
    title="VOCES — Facultad de Ingeniería",
    description="Visibilización de problemáticas de género (Universidad Distrital Francisco José de Caldas)",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(SessionMiddleware, secret_key=settings.secret_key)
app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=["*"] if settings.is_development() else ["localhost", "127.0.0.1"],
)
app.mount("/static", StaticFiles(directory="app/static"), name="static")

# Routers (definidos en app/routers/).
from app.routers import public, admin  # noqa: E402

app.include_router(public.router)
app.include_router(admin.router)
