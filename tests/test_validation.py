"""Tests de validación del formulario de reporte."""

def test_reporte_valido(client):
    response = client.post(
        "/reportar",
        data={
            "content": "Un comentario sexista inapropiado en el salon de clases.",
            "category": "comentario_sexista",
            "place": "salon",
            "actor_role": "estudiante",
            "period": "2024-1",
            "is_witness": "true",
            "career": "Ingenieria de Sistemas",
            "semester": "4",
            "csrf_token": "test-csrf",
        },
        follow_redirects=False,
    )
    assert response.status_code == 200
    assert b"Gracias por compartirlo" in response.content


def test_reporte_campos_faltantes(client):
    response = client.post(
        "/reportar",
        data={
            "content": "",
            "category": "comentario_sexista",
            "place": "salon",
            "csrf_token": "test-csrf",
        },
        follow_redirects=False,
    )
    assert response.status_code == 400


def test_reporte_texto_demasiado_largo(client):
    response = client.post(
        "/reportar",
        data={
            "content": "x" * 501,
            "category": "comentario_sexista",
            "place": "salon",
            "csrf_token": "test-csrf",
        },
        follow_redirects=False,
    )
    assert response.status_code == 400


def test_reporte_sin_csrf(client):
    response = client.post(
        "/reportar",
        data={
            "content": "Un comentario sexista en el salon.",
            "category": "comentario_sexista",
            "place": "salon",
        },
        follow_redirects=False,
    )
    assert response.status_code == 403


def test_muro_publico(client):
    response = client.get("/")
    assert response.status_code == 200
    assert b"Lo que se escucha" in response.content


def test_categorias_page(client):
    response = client.get("/categorias")
    assert response.status_code == 200
    assert "Por qué es problemático".encode() in response.content


def test_apoyo_page(client):
    response = client.get("/apoyo")
    assert response.status_code == 200
    assert "Directorio de apoyo".encode() in response.content


def test_encuesta_page(client):
    response = client.get("/encuesta")
    assert response.status_code == 200
    assert "Encuesta de percepción".encode() in response.content

