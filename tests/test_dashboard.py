"""Tests para el umbral mínimo del dashboard y estadísticas agregadas."""

from app.services.stats import dashboard_summary, _low_count_filter


def test_umbral_minimo_oculta_grupos_pequenos():
    """Grupos con menos de 5 casos deben ocultarse (umbral mínimo)."""
    assert _low_count_filter(3) is None
    assert _low_count_filter(4) is None
    assert _low_count_filter(5) == 5
    assert _low_count_filter(10) == 10


def test_dashboard_con_datos_demo(client):
    """El dashboard requiere autenticación de administrador."""
    response = client.get("/admin", follow_redirects=False)
    assert response.status_code in (303, 307)


def test_dashboard_summary_structure(db_session):
    """El dashboard aplica el umbral mínimo de 5 casos por grupo."""
    from app.models import Report, ReportStatus, AdminUser
    from app.services.auth import get_password_hash

    db = db_session
    db.add(AdminUser(username="admin", password_hash=get_password_hash("testpassword123"), is_active=True))

    # Insertar reportes aprobados: 6 de una categoria, 2 de otra (debajo del umbral)
    for _ in range(6):
        db.add(Report(
            content="Comentario sexista demo",
            category="comentario_sexista",
            place="salon",
            status=ReportStatus.aprobado,
            is_demo=True,
        ))
    for _ in range(2):
        db.add(Report(
            content="Acoso verbal demo",
            category="acoso_verbal",
            place="cafeteria",
            status=ReportStatus.aprobado,
            is_demo=True,
        ))
    db.commit()

    summary = dashboard_summary(db)

    total = summary["total_reports"]
    assert total == 8

    # La categoría con 6 casos debe mostrarse
    categorias = {c["category"]: c for c in summary["by_category"]}
    assert "comentario_sexista" in categorias
    assert categorias["comentario_sexista"]["count"] == 6

    # La categoría con 2 casos debe estar oculta (count=0, hidden=True)
    assert "acoso_verbal" in categorias
    assert categorias["acoso_verbal"]["hidden"] is True
    assert categorias["acoso_verbal"]["count"] == 0
