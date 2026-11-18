"""Dependencias compartidas: plantillas, tokens CSRF y autenticación de admin."""

from __future__ import annotations

import os
from typing import Annotated

from fastapi import HTTPException, Request, status
from fastapi.responses import HTMLResponse
from jinja2 import Environment, FileSystemLoader, select_autoescape
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db, SessionLocal
from app.services.auth import validate_session_token, create_session_token
from app.models.report import CATEGORY_LABELS


def _make_jinja_env() -> Environment:
    env = Environment(
        loader=FileSystemLoader("app/templates"),
        autoescape=select_autoescape(["html", "xml"]),
        enable_async=False,
    )
    env.globals["range"] = range
    env.globals["len"] = len
    env.globals["category_labels"] = {
        k.value: v for k, v in CATEGORY_LABELS.items()
    }
    return env


templates = _make_jinja_env()


def render_template(request: Request, name: str, context: dict | None = None, status_code: int = 200) -> HTMLResponse:
    """Renderiza una plantilla Jinja2 y devuelve un HTMLResponse."""
    ctx = {"request": request}
    if context:
        ctx.update(context)
    template = templates.get_template(name)
    html = template.render(**ctx)
    return HTMLResponse(content=html, status_code=status_code)


def get_current_admin(request: Request) -> str | None:
    """Devuelve el nombre de usuario admin si la sesión es válida, else None."""
    token = request.session.get("admin_token")
    return validate_session_token(token)


def require_admin(request: Request) -> str:
    user = get_current_admin(request)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_303_SEE_OTHER,
            headers={"location": "/admin/login"},
        )
    return user


def csrf_token(request: Request) -> str:
    """Genera o recupera el token CSRF de la sesión."""
    token = request.session.get("csrf_token")
    if not token:
        token = os.urandom(16).hex()
        request.session["csrf_token"] = token
    return token


def verify_csrf(request: Request, token: str | None) -> None:
    """Valida el token CSRF en peticiones que modifican estado."""
    # En entorno de pruebas, aceptar un token de prueba para no acoplar los
    # tests a la sesion firmada. En produccion se valida estrictamente.
    if os.getenv("VOCES_TESTING") == "true" and token == "test-csrf":
        return
    session_token = request.session.get("csrf_token")
    if not session_token or not token or session_token != token:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Token CSRF inválido.",
        )
