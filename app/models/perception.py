"""Respuestas de la encuesta corta de percepción (agregadas, anónimas)."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Optional

from sqlalchemy import Boolean, DateTime, Integer, JSON, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class PerceptionResponse(Base):
    __tablename__ = "perception_responses"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    # Respuestas guardadas como JSON: { pregunta_id: valor (1-5) }
    answers: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    is_demo: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False
    )
