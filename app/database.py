"""Conexión a la base de datos SQLite con SQLAlchemy.

Las tablas se crean automáticamente al iniciar la aplicación (create_all).
Para entornos de producción se recomienda gestionar migraciones con Alembic.
"""

from __future__ import annotations

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker, Session

from app.config import settings


class Base(DeclarativeBase):
    pass


engine = create_engine(
    settings.database_url,
    connect_args={"check_same_thread": False} if settings.database_url.startswith("sqlite") else {},
    echo=settings.is_development(),
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db() -> Session:
    """Provee una sesión de base de datos por petición (dependency de FastAPI)."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db() -> None:
    """Crea todas las tablas definidas en los modelos."""
    import app.models  # noqa: F401  asegura que los modelos estén registrados

    Base.metadata.create_all(bind=engine)
