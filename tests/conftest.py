"""Configuración y fixtures compartidos para los tests de pytest."""

from __future__ import annotations

import os
import tempfile

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

os.environ["VOCES_ADMIN_PASSWORD"] = "testpassword123"
os.environ["VOCES_SECRET_KEY"] = "test-secret-key"
os.environ["VOCES_DEBUG"] = "true"
os.environ["VOCES_TESTING"] = "true"

from app.database import Base  # noqa: E402
from app.main import app  # noqa: E402


@pytest.fixture(scope="function")
def db_session():
    """Crea una base de datos SQLite temporal aislada por test."""
    fd, db_path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    database_url = f"sqlite:///{db_path}"

    engine = create_engine(database_url, connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    connection = engine.connect()
    transaction = connection.begin()
    TestingSessionLocal = sessionmaker(bind=connection)
    session = TestingSessionLocal()

    # Sobrescribir el engine y SessionLocal de app.database para este test
    import app.database as database_module

    original_engine = database_module.engine
    original_session_local = database_module.SessionLocal
    database_module.engine = engine
    database_module.SessionLocal = TestingSessionLocal

    yield session

    session.close()
    transaction.rollback()
    connection.close()
    engine.dispose()

    # Restaurar
    database_module.engine = original_engine
    database_module.SessionLocal = original_session_local

    # Borrar archivo temporal (ahora sin conexiones abiertas)
    try:
        os.remove(db_path)
    except PermissionError:
        pass


@pytest.fixture
def client(db_session):
    """Devuelve un TestClient de FastAPI con la DB de test."""

    def override_get_db():
        yield db_session

    import app.database as database_module

    app.dependency_overrides[database_module.get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture
def admin_session(client, db_session):
    """Inicia sesión como admin y devuelve el client con cookies de sesión."""
    from app.models import AdminUser
    from app.services.auth import get_password_hash

    db = db_session
    db.add(
        AdminUser(
            username="admin",
            password_hash=get_password_hash("testpassword123"),
            is_active=True,
        )
    )
    db.commit()

    # Login mediante el test client
    client.post(
        "/admin/login",
        data={
            "username": "admin",
            "password": "testpassword123",
            "csrf_token": "test-csrf",
        },
        follow_redirects=False,
    )
    return client
