"""Rutas públicas de VOCES: muro, reporte, categorías, apoyo, encuesta, votos."""

from __future__ import annotations

import os
import hashlib

from fastapi import APIRouter, Request, Depends, Form, HTTPException, status
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import (
    Report,
    ReportStatus,
    Place,
    CategoryInfo,
    SupportResource,
    CATEGORY_LABELS,
)
from app.models.vote import Vote
from app.services.pii import scan_pii, looks_like_accusation
from app.services.rate_limit import rate_limiter
from app.dependencies import csrf_token, verify_csrf, render_template

router = APIRouter()

PER_PAGE = 12


def _get_places(db: Session):
    return db.query(Place).filter(Place.is_active == True).order_by(Place.order_index).all()  # noqa: E712


@router.get("/", response_class=HTMLResponse, name="wall")
def wall(
    request: Request,
    db: Session = Depends(get_db),
    category: str | None = None,
    place: str | None = None,
    period: str | None = None,
    page: int = 1,
):
    """Muro público: reportes aprobados, paginados y con filtros."""
    query = db.query(Report).filter(Report.status == ReportStatus.aprobado)
    if category:
        query = query.filter(Report.category == category)
    if place:
        query = query.filter(Report.place == place)
    if period:
        query = query.filter(Report.period == period)

    total = query.count()
    pages = max(1, -(-total // PER_PAGE)) if total else 1
    page = max(1, min(page, pages))
    offset = (page - 1) * PER_PAGE
    reports = query.order_by(Report.created_at.desc()).offset(offset).limit(PER_PAGE).all()

    places = _get_places(db)
    periods = [p[0] for p in db.query(Report.period).distinct().all() if p[0]]

    return render_template(request,
        "wall.html",
        {
            "request": request,
            "title": "Lo que se escucha",
            "reports": reports,
            "places": places,
            "periods": periods,
            "category_labels": CATEGORY_LABELS,
            "current_category": category,
            "current_place": place,
            "current_period": period,
            "page": page,
            "pages": pages,
            "total": total,
            "per_page": PER_PAGE,
            "csrf_token": csrf_token(request),
        },
    )


@router.get("/reportar", response_class=HTMLResponse, name="report_form")
def report_form(request: Request):
    """Formulario de reporte anónimo."""
    return render_template(request,
        "report.html",
        {
            "request": request,
            "title": "Reportar de forma anónima",
            "categories": list(CATEGORY_LABELS.items()),
            "csrf_token": csrf_token(request),
        },
    )


@router.post("/reportar", name="submit_report")
async def submit_report(request: Request, db: Session = Depends(get_db)):
    """Recibe un reporte anónimo, aplica PII y rate limiting, lo guarda como pendiente."""
    client_ip = request.client.host if request.client else "unknown"
    if not rate_limiter.is_allowed(client_ip):
        raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail="Demasiadas solicitudes. Inténtalo más tarde.")

    form = await request.form()
    verify_csrf(request, form.get("csrf_token"))

    content = (form.get("content") or "").strip()
    category = form.get("category")
    place = form.get("place")
    actor_role = form.get("actor_role") or None
    period = form.get("period") or None
    is_witness_raw = form.get("is_witness")
    is_witness = is_witness_raw == "true" if is_witness_raw else None
    career = form.get("career") or None
    semester = form.get("semester") or None

    if not content or not category or not place:
        raise HTTPException(status_code=400, detail="Campos obligatorios incompletos.")
    if len(content) > 500:
        raise HTTPException(status_code=400, detail="El texto supera los 500 caracteres.")

    # Detección y censura de PII.
    censored, findings, pii_flagged = scan_pii(content)
    if looks_like_accusation(censored):
        pii_flagged = True

    if not censored.strip():
        raise HTTPException(status_code=400, detail="Tras eliminar datos personales no queda contenido válido.")

    report = Report(
        content=censored,
        category=category,
        place=place,
        actor_role=actor_role,
        period=period,
        is_witness=is_witness,
        career=career,
        semester=semester,
        pii_flagged=pii_flagged,
        is_demo=False,
    )
    db.add(report)
    db.commit()
    db.refresh(report)

    return render_template(request,
        "report_sent.html",
        {
            "request": request,
            "title": "Reporte enviado",
            "report_id": report.id,
            "pii_flagged": pii_flagged,
        },
    )


@router.get("/categorias", response_class=HTMLResponse, name="categories_page")
def categories_page(request: Request, db: Session = Depends(get_db)):
    """Sección '¿Por qué es problemático?' con explicaciones pedagógicas."""
    cats = (
        db.query(CategoryInfo)
        .filter(CategoryInfo.is_active == True)
        .order_by(CategoryInfo.order_index)
        .all()
    )  # noqa: E712
    return render_template(request,
        "categories.html",
        {"request": request, "title": "¿Por qué es problemático?", "categories": cats},
    )


@router.get("/apoyo", response_class=HTMLResponse, name="support_page")
def support_page(request: Request, db: Session = Depends(get_db)):
    """Directorio de apoyo (rutas de atención)."""
    resources = (
        db.query(SupportResource)
        .filter(SupportResource.is_active == True)
        .order_by(SupportResource.order_index)
        .all()
    )  # noqa: E712
    return render_template(request,
        "support.html",
        {"request": request, "title": "Directorio de apoyo", "resources": resources},
    )


@router.get("/encuesta", response_class=HTMLResponse, name="perception_form")
def perception_form(request: Request):
    """Encuesta corta de percepción (8 preguntas)."""
    questions = [
        {"id": "q1", "text": "Me siento seguro/a en mi salón de clases."},
        {"id": "q2", "text": "He visto trato desigual entre géneros en la facultad."},
        {"id": "q3", "text": "Conozco los canales de denuncia de la universidad."},
        {"id": "q4", "text": "Los docentes promueven un ambiente respetuoso."},
        {"id": "q5", "text": "Me sentiría cómodo/a denunciando una situación de género."},
        {"id": "q6", "text": "He sido testigo de comentarios sexistas en la sede."},
        {"id": "q7", "text": "Siento que la facultad toma en serio el tema de género."},
        {"id": "q8", "text": "Conozco a alguien a quien le haya pasado algo similar."},
    ]
    return render_template(request,
        "perception.html",
        {
            "request": request,
            "title": "Encuesta de percepción",
            "questions": questions,
            "csrf_token": csrf_token(request),
        },
    )


@router.post("/encuesta", name="submit_perception")
async def submit_perception(request: Request, db: Session = Depends(get_db)):
    form = await request.form()
    verify_csrf(request, form.get("csrf_token"))
    answers = {}
    for i in range(1, 9):
        v = form.get(f"q{i}")
        if v in ("1", "2", "3", "4", "5"):
            answers[f"q{i}"] = int(v)
    if len(answers) < 8:
        raise HTTPException(status_code=400, detail="Debes responder todas las preguntas.")
    from app.models import PerceptionResponse

    db.add(PerceptionResponse(answers=answers, is_demo=False))
    db.commit()
    return render_template(request,
        "perception_sent.html",
        {"request": request, "title": "Gracias por tu respuesta"},
    )


@router.get("/como-actuar", response_class=HTMLResponse, name="como_actuar")
def como_actuar(request: Request):
    """Guía de intervención de espectador si presencias una situación de género."""
    return render_template(request, "como_actuar.html", {"request": request, "title": "Cómo actuar si presencias una situación"})


@router.post("/votar/{report_id}", name="vote_report")
async def vote_report(request: Request, report_id: int, db: Session = Depends(get_db)):
    """Voto anónimo 'a mí también me pasó' (uno por dispositivo y reporte)."""
    client_ip = request.client.host if request.client else "unknown"
    device_hash = hashlib.sha256(client_ip.encode()).hexdigest()[:32]

    exists = (
        db.query(Vote)
        .filter(Vote.report_id == report_id, Vote.device_hash == device_hash)
        .first()
    )
    if exists:
        count = db.query(Vote).filter(Vote.report_id == report_id).count()
        return JSONResponse({"ok": False, "count": count, "message": "Ya votaste en este reporte."})

    db.add(Vote(report_id=report_id, device_hash=device_hash))
    db.commit()
    count = db.query(Vote).filter(Vote.report_id == report_id).count()
    return JSONResponse({"ok": True, "count": count})
