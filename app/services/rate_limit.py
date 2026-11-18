"""Rate limiter en memoria con hash de IP y sal rotativa no persistida.

La IP nunca se guarda en la base de datos. Solo se mantiene un hash con una
sal que se regenera al iniciar la aplicación y periódicamente (cada hora), por lo
que no es posible reconstruir direcciones IP a partir de los datos almacenados.
"""

from __future__ import annotations

import hashlib
import os
import time
from collections import defaultdict

from app.config import settings


class RateLimiter:
    def __init__(self, max_requests: int, window_seconds: int) -> None:
        self.max_requests = max_requests
        self.window = window_seconds
        self._salt = os.urandom(16).hex()
        self._last_rotation = time.time()
        self._buckets: dict[str, list[float]] = defaultdict(list)

    def _rotate_salt_if_needed(self) -> None:
        if time.time() - self._last_rotation > 3600:  # 1 hora
            self._salt = os.urandom(16).hex()
            self._last_rotation = time.time()
            self._buckets.clear()

    def _key(self, ip: str) -> str:
        return hashlib.sha256((ip + self._salt).encode("utf-8")).hexdigest()

    def is_allowed(self, ip: str) -> bool:
        self._rotate_salt_if_needed()
        now = time.time()
        key = self._key(ip)
        window_start = now - self.window
        timestamps = [t for t in self._buckets[key] if t > window_start]
        self._buckets[key] = timestamps
        if len(timestamps) >= self.max_requests:
            return False
        timestamps.append(now)
        return True


rate_limiter = RateLimiter(
    max_requests=settings.rate_limit_requests,
    window_seconds=settings.rate_limit_window,
)
