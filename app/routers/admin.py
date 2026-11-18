"""Rutas de administración de VOCES: login, moderación, dashboard, exportación, apoyo."""

from __future__ import annotations

import datetime
from fastapi import APIRouter, Request, Depends, HTTPException, status
from fastapi.responses import HTMLResponse, RedirectResponse, Response
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import (
    Report,
    ReportStatus,
    AdminUser,
    SupportResource,
)
from app.models.vote import Vote
from app.services.auth import verify_password, create_session_token, validate_session_token
from app.services.stats import dashboard_summary
from app.services.export import export_pdf, export_csv_anonymized
from app.services.pii import scan_pii
from app.dependencies import csrf_token, verify_csrf, render_template, require_admin

router = APIRouter(prefix="/admin")


def _get_admin(request: Request, db: Session) -> AdminUser | None:
    token = request.session.get("admin_token")
    username = validate_session_token(token)
    if not username:
        return None
    return db.query(AdminUser).filter(AdminUser.username == username, AdminUser.is_active == True).first()  # noqa: E712


@router.get("/login", response_class=HTMLResponse, name="admin_login_form")
def admin_login_form(request: Request):
    return render_template(request,
        "admin/login.html",
        {"request": request, "title": "Iniciar sesión — Admin", "csrf_token": csrf_token(request)},
    )


@router.post("/login", name="admin_login")
async def admin_login(request: Request, db: Session = Depends(get_db)):
    form = await request.form()
    verify_csrf(request, form.get("csrf_token"))
    username = form.get("username")
    password = form.get("password")
    admin = db.query(AdminUser).filter(AdminUser.username == username).first()
    if not admin or not admin.is_active or not verify_password(password or "", admin.password_hash):
        raise HTTPException(status_code=401, detail="Credenciales inválidas.")
    admin.last_login = datetime.datetime.now()
    db.add(admin)
    db.commit()
    request.session["admin_token"] = create_session_token(username)
    request.session["admin_user"] = username
    return RedirectResponse(url="/admin", status_code=status.HTTP_303_SEE_OTHER)


@router.get("/logout", name="admin_logout")
def admin_logout(request: Request):
    request.session.clear()
    return RedirectResponse(url="/admin/login", status_code=status.HTTP_303_SEE_OTHER)


@router.get("/", response_class=HTMLResponse, name="admin_dashboard")
def admin_dashboard(request: Request, db: Session = Depends(get_db), _: str = Depends(require_admin)):
    summary = dashboard_summary(db)
    return render_template(request,
        "admin/dashboard.html",
        {"request": request, "title": "Panel de administración", "summary": summary},
    )


@router.get("/moderacion", response_class=HTMLResponse, name="moderation_queue")
def moderation_queue(request: Request, db: Session = Depends(get_db), _: str = Depends(require_admin)):
    reports = db.query(Report).order_by(Report.created_at.asc()).all()
    return render_template(request,
        "admin/moderation.html",
        {"request": request, "title": "Cola de moderación", "reports": reports},
    )


@router.post("/moderacion/{report_id}", name="moderate_report")
async def moderate_report(
    request: Request, report_id: int, db: Session = Depends(get_db), _: str = Depends(require_admin)
):
    form = await request.form()
    verify_csrf(request, form.get("csrf_token"))
    action = form.get("action")  # aprobar | rechazar | editar
    report = db.query(Report).filter(Report.id == report_id).first()
    if not report:
        raise HTTPException(status_code=404, detail="Reporte no encontrado.")
    if action == "aprobar":
        report.status = ReportStatus.aprobado
    elif action == "rechazar":
        report.status = ReportStatus.rechazado
    elif action == "editar":
        new_content = (form.get("content") or "").strip()
        censored, _, pii_flagged = scan_pii(new_content)
        report.content = censored
        report.pii_flagged = pii_flagged
        report.status = ReportStatus.aprobado
    report.moderator_notes = form.get("notes") or None
    db.add(report)
    db.commit()
    return RedirectResponse(url="/admin/moderacion", status_code=status.HTTP_303_SEE_OTHER)


@router.get("/export/pdf", name="export_pdf")
def export_pdf_route(request: Request, db: Session = Depends(get_db), _: str = Depends(require_admin)):
    pdf = export_pdf(db)
    return Response(
        content=pdf,
        media_type="application/pdf",
        headers={"Content-Disposition": "attachment; filename=voces_informe.pdf"},
    )


@router.get("/export/csv", name="export_csv")
def export_csv_route(request: Request, db: Session = Depends(get_db), _: str = Depends(require_admin)):
    csv_data = export_csv_anonymized(db)
    return Response(
        content=csv_data,
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=voces_reportes_anonimizados.csv"},
    )


@router.get("/apoyo", response_class=HTMLResponse, name="admin_support")
def admin_support(request: Request, db: Session = Depends(get_db), _: str = Depends(require_admin)):
    resources = db.query(SupportResource).order_by(SupportResource.order_index).all()
    return render_template(request,
        "admin/support.html",
        {"request": request, "title": "Gestionar directorio de apoyo", "resources": resources},
    )


@router.post("/apoyo", name="admin_support_save")
async def admin_support_save(
    request: Request, db: Session = Depends(get_db), _: str = Depends(require_admin)
):
    form = await request.form()
    verify_csrf(request, form.get("csrf_token"))
    resource_id = form.get("id")
    title = form.get("title")
    description = form.get("description")
    resource_type = form.get("resource_type")
    phone = form.get("phone") or None
    email = form.get("email") or None
    url = form.get("url") or None
    is_placeholder = form.get("is_placeholder") == "on"
    is_active = form.get("is_active") == "on"
    order_index = int(form.get("order_index") or 0)

    if not title or not description or not resource_type:
        raise HTTPException(status_code=400, detail="Campos obligatorios incompletos.")

    if resource_id:
        res = db.query(SupportResource).filter(SupportResource.id == int(resource_id)).first()
        if res:
            res.title = title
            res.description = description
            res.resource_type = resource_type
            res.phone = phone
            res.email = email
            res.url = url
            res.is_placeholder = is_placeholder
            res.is_active = is_active
            res.order_index = order_index
            db.add(res)
    else:
        db.add(
            SupportResource(
                title=title,
                description=description,
                resource_type=resource_type,
                phone=phone,
                email=email,
                url=url,
                is_placeholder=is_placeholder,
                is_active=is_active,
                order_index=order_index,
            )
        )
    db.commit()
    return RedirectResponse(url="/admin/apoyo", status_code=status.HTTP_303_SEE_OTHER)
