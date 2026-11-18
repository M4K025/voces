"""Autenticación de administración y sesiones firmadas.

La contraseña de administrador proviene exclusivamente de la variable de entorno
VOCES_ADMIN_PASSWORD y se almacena con hash bcrypt. La sesión es una cookie
firmada con itsdangerous (expirable, HttpOnly, SameSite=Lax).
"""

from __future__ import annotations

from datetime import datetime

import bcrypt
from itsdangerous import URLSafeTimedSerializer, BadSignature, SignatureExpired

from app.config import settings

serializer = URLSafeTimedSerializer(settings.secret_key)


def get_password_hash(password: str) -> str:
    """Devuelve el hash bcrypt de la contraseña."""
    pwd = password.encode("utf-8")
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(pwd, salt).decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verifica una contraseña contra su hash bcrypt."""
    try:
        return bcrypt.checkpw(
            plain_password.encode("utf-8"), hashed_password.encode("utf-8")
        )
    except Exception:
        return False


def create_session_token(username: str) -> str:
    """Genera un token de sesión firmado con expiración."""
    return serializer.dumps({"user": username})


def validate_session_token(token: str | None, max_age: int | None = None) -> str | None:
    """Valida el token y devuelve el nombre de usuario si es válido."""
    if not token:
        return None
    try:
        data = serializer.loads(token, max_age=max_age or settings.session_max_age)
        return str(data.get("user", "")) or None
    except (BadSignature, SignatureExpired):
        return None


def require_admin_password() -> str:
    """Devuelve la contraseña configurada (útil para crear el primer admin)."""
    if not settings.admin_password:
        raise RuntimeError("VOCES_ADMIN_PASSWORD no está definida.")
    return settings.admin_password
