"""Cálculo de estadísticas agregadas para el dashboard público y de administración.

Regla de privacidad: se omite cualquier grupo con menos de
VOCES_DASHBOARD_MIN_GROUP (por defecto 5) casos para evitar re-identificación.
"""

from __future__ import annotations

from collections import Counter
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.config import settings
from app.models.report import Report, ReportStatus, CATEGORY_LABELS, ReportCategory
from app.models.perception import PerceptionResponse


def _low_count_filter(count: int) -> int | None:
    """Devuelve None si el grupo tiene menos casos del umbral mínimo."""
    if count < settings.dashboard_min_group:
        return None
    return count


def total_reports(db: Session, approved_only: bool = True) -> int:
    stmt = select(func.count(Report.id))
    if approved_only:
        stmt = stmt.where(Report.status == ReportStatus.aprobado)
    return db.execute(stmt).scalar() or 0


def reports_by_category(db: Session) -> list[dict[str, Any]]:
    stmt = (
        select(Report.category, func.count(Report.id))
        .where(Report.status == ReportStatus.aprobado)
        .group_by(Report.category)
    )
    rows = db.execute(stmt).all()
    result = []
    for category, count in rows:
        c = _low_count_filter(count)
        result.append(
            {
                "category": category.value if category else "otro",
                "label": CATEGORY_LABELS.get(category, category.value if category else "otro"),
                "count": c if c is not None else 0,
                "hidden": c is None,
            }
        )
    return result


def reports_by_place(db: Session) -> list[dict[str, Any]]:
    stmt = (
        select(Report.place, func.count(Report.id))
        .where(Report.status == ReportStatus.aprobado)
        .group_by(Report.place)
    )
    rows = db.execute(stmt).all()
    result = []
    for place, count in rows:
        c = _low_count_filter(count)
        result.append(
            {
                "place": place,
                "count": c if c is not None else 0,
                "hidden": c is None,
            }
        )
    return result


def reports_by_actor_role(db: Session) -> list[dict[str, Any]]:
    stmt = (
        select(Report.actor_role, func.count(Report.id))
        .where(Report.status == ReportStatus.aprobado)
        .where(Report.actor_role.is_not(None))
        .group_by(Report.actor_role)
    )
    rows = db.execute(stmt).all()
    result = []
    for role, count in rows:
        c = _low_count_filter(count)
        result.append(
            {
                "actor_role": role or "no_sabe",
                "count": c if c is not None else 0,
                "hidden": c is None,
            }
        )
    return result


def reports_over_time(db: Session) -> list[dict[str, Any]]:
    stmt = (
        select(Report.period, func.count(Report.id))
        .where(Report.status == ReportStatus.aprobado)
        .where(Report.period.is_not(None))
        .group_by(Report.period)
        .order_by(Report.period)
    )
    rows = db.execute(stmt).all()
    result = []
    for period, count in rows:
        c = _low_count_filter(count)
        result.append(
            {
                "period": period,
                "count": c if c is not None else 0,
                "hidden": c is None,
            }
        )
    return result


def top_phrases(db: Session, limit: int = 10) -> list[str]:
    """Frases más frecuentes entre reportes aprobados.

    Nota: como los textos son libres, aquí se devuelven los textos completos
    ordenados por frecuencia. Se aplica el umbral de grupo implícito al no
    mostrar frases que aparezcan menos veces que el mínimo.
    """
    stmt = select(Report.content, func.count(Report.id)).where(
        Report.status == ReportStatus.aprobado
    ).group_by(Report.content).order_by(func.count(Report.id).desc()).limit(limit)
    rows = db.execute(stmt).all()
    result = []
    for content, count in rows:
        if _low_count_filter(count) is not None:
            result.append(content)
    return result


def perception_stats(db: Session) -> dict[str, Any]:
    """Estadísticas agregadas de la encuesta de percepción (promedio por pregunta)."""
    stmt = select(PerceptionResponse.answers).where(
        PerceptionResponse.is_demo == False  # noqa: E712
    )
    rows = db.execute(stmt).scalars().all()
    totals: dict[str, list[int]] = {}
    for answers in rows:
        for qid, value in answers.items():
            try:
                v = int(value)
            except (TypeError, ValueError):
                continue
            totals.setdefault(qid, []).append(v)
    result = {}
    for qid, values in totals.items():
        result[qid] = {
            "average": round(sum(values) / len(values), 2),
            "count": len(values),
            "min": min(values),
            "max": max(values),
        }
    return result


def dashboard_summary(db: Session) -> dict[str, Any]:
    return {
        "total_reports": total_reports(db, approved_only=True),
        "pending_reports": total_reports(db, approved_only=False)
        - total_reports(db, approved_only=True),
        "by_category": reports_by_category(db),
        "by_place": reports_by_place(db),
        "by_actor_role": reports_by_actor_role(db),
        "over_time": reports_over_time(db),
        "top_phrases": top_phrases(db),
        "perception": perception_stats(db),
        "min_group": settings.dashboard_min_group,
    }
