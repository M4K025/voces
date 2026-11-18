"""Tests para la cola de moderación y el panel de administración."""

from app.models import AdminUser, Report, ReportStatus
from app.services.auth import get_password_hash


def _crear_admin(db):
    db.add(
        AdminUser(
            username="admin",
            password_hash=get_password_hash("testpassword123"),
            is_active=True,
        )
    )
    db.commit()


def test_admin_login(client, db_session):
    _crear_admin(db_session)
    response = client.post(
        "/admin/login",
        data={
            "username": "admin",
            "password": "testpassword123",
            "csrf_token": "test-csrf",
        },
        follow_redirects=False,
    )
    assert response.status_code in (303, 307)  # Redirect a /admin


def test_admin_login_credenciales_invalidas(client, db_session):
    _crear_admin(db_session)
    response = client.post(
        "/admin/login",
        data={
            "username": "admin",
            "password": "wrongpassword",
            "csrf_token": "test-csrf",
        },
        follow_redirects=False,
    )
    assert response.status_code == 401


def test_moderacion_queue_requiere_auth(client, db_session):
    response = client.get("/admin/moderacion", follow_redirects=False)
    assert response.status_code in (303, 307)  # Redirect a /admin/login


def test_aprobar_reporte(admin_session, db_session):
    db = db_session
    reporte = Report(
        content="Comentario sexista de prueba",
        category="comentario_sexista",
        place="salon",
        status=ReportStatus.pendiente,
        is_demo=False,
    )
    db.add(reporte)
    db.commit()
    reporte_id = reporte.id

    response = admin_session.post(
        f"/admin/moderacion/{reporte_id}",
        data={
            "action": "aprobar",
            "csrf_token": "test-csrf",
        },
        follow_redirects=False,
    )
    assert response.status_code in (303, 307)  # Redirect a /admin/moderacion

    # Verificar en la misma sesion (compartida con el override de get_db)
    r = db.query(Report).filter(Report.id == reporte_id).first()
    assert r.status == ReportStatus.aprobado


def test_rechazar_reporte(admin_session, db_session):
    db = db_session
    reporte = Report(
        content="Contenido de prueba para rechazar",
        category="otro",
        place="cafeteria",
        status=ReportStatus.pendiente,
        is_demo=False,
    )
    db.add(reporte)
    db.commit()
    reporte_id = reporte.id

    response = admin_session.post(
        f"/admin/moderacion/{reporte_id}",
        data={
            "action": "rechazar",
            "csrf_token": "test-csrf",
        },
        follow_redirects=False,
    )
    assert response.status_code == 303

    r = db.query(Report).filter(Report.id == reporte_id).first()
    assert r.status == ReportStatus.rechazado


def test_editar_y_aprobar_reporte_censura_pii(admin_session, db_session):
    db = db_session
    reporte = Report(
        content="Texto original",
        category="comentario_sexista",
        place="salon",
        status=ReportStatus.pendiente,
        is_demo=False,
    )
    db.add(reporte)
    db.commit()
    reporte_id = reporte.id

    response = admin_session.post(
        f"/admin/moderacion/{reporte_id}",
        data={
            "action": "editar",
            "content": "Juan Perez dijo algo inapropiado",  # Tiene nombre propio
            "csrf_token": "test-csrf",
        },
        follow_redirects=False,
    )
    assert response.status_code == 303

    r = db.query(Report).filter(Report.id == reporte_id).first()
    assert r.status == ReportStatus.aprobado
    assert "[NOMBRE OMITIDO]" in r.content
    assert "Juan Perez" not in r.content
    assert r.pii_flagged is True
