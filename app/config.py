"""Configuración de la aplicación a partir de variables de entorno.

Nunca se almacenan secretos hardcodeados. La contraseña de administración
debe suministrarse mediante la variable VOCES_ADMIN_PASSWORD.
"""

from __future__ import annotations

import os
from functools import lru_cache


class Settings:
    def __init__(self) -> None:
        self.app_name = os.getenv("VOCES_APP_NAME", "VOCES — Facultad de Ingeniería")
        self.database_url = os.getenv("VOCES_DATABASE_URL", "sqlite:///./voces.db")
        self.secret_key = os.getenv("VOCES_SECRET_KEY")
        if not self.secret_key:
            # Clave solo para desarrollo local; en producción definir VOCES_SECRET_KEY.
            self.secret_key = "dev-insecure-secret-key-change-me"
        self.admin_username = os.getenv("VOCES_ADMIN_USERNAME", "admin")
        self.admin_password = os.getenv("VOCES_ADMIN_PASSWORD")
        if not self.admin_password:
            raise RuntimeError(
                "Falta la variable de entorno VOCES_ADMIN_PASSWORD. "
                "Defínala antes de iniciar la aplicación (nunca se hardcodea)."
            )
        self.session_cookie_name = os.getenv("VOCES_SESSION_COOKIE_NAME", "voces_session")
        self.session_max_age = int(os.getenv("VOCES_SESSION_MAX_AGE", "3600"))  # segundos
        # Rate limiting: solicitudes por ventana por IP (hash, no se persiste IP).
        self.rate_limit_requests = int(os.getenv("VOCES_RATE_LIMIT_REQUESTS", "20"))
        self.rate_limit_window = int(os.getenv("VOCES_RATE_LIMIT_WINDOW", "60"))  # segundos
        self.dashboard_min_group = int(os.getenv("VOCES_DASHBOARD_MIN_GROUP", "5"))
        self.debug = os.getenv("VOCES_DEBUG", "false").lower() in ("1", "true", "yes")

    def is_development(self) -> bool:
        return self.debug


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
