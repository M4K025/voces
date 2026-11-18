"""Tests para la detección y censura de datos personales (PII)."""

from app.services.pii import scan_pii, looks_like_accusation


def test_censura_email():
    texto = "Contactame a juan.perez@correo.edu.co"
    censurado, count, flagged = scan_pii(texto)
    assert "[EMAIL OMITIDO]" in censurado
    assert "juan.perez@correo.edu.co" not in censurado
    assert count >= 1


def test_censura_telefono():
    texto = "Llama al 3001234567 o al +57 310 987 65 43"
    censurado, count, flagged = scan_pii(texto)
    assert "[TELÉFONO OMITIDO]" in censurado
    assert count >= 1


def test_censura_codigo_estudiantil():
    texto = "Mi codigo es 2020123456 y el de ella es 2019876543"
    censurado, count, flagged = scan_pii(texto)
    assert "[CÓDIGO OMITIDO]" in censurado
    assert "2020123456" not in censurado
    assert count >= 2


def test_censura_nombre_propio():
    texto = "Maria Garcia dijo algo inapropiado en el salon"
    censurado, count, flagged = scan_pii(texto)
    assert "[NOMBRE OMITIDO]" in censurado
    assert "Maria Garcia" not in censurado
    assert flagged is True  # nombre propio -> pii_flagged


def test_sin_pii_no_flagged():
    texto = "El docente hizo un comentario sexista en el salon de clases"
    censurado, count, flagged = scan_pii(texto)
    assert flagged is False
    assert count == 0


def test_texto_vacio():
    censurado, count, flagged = scan_pii("")
    assert censurado == ""
    assert count == 0
    assert flagged is False


def test_looks_like_accusation():
    assert looks_like_accusation("Funa a Juan Perez") is True
    assert looks_like_accusation("Denuncio al docente") is True
    assert looks_like_accusation("Un comentario sexista en el salon") is False


def test_pii_flagged_con_nombre():
    texto = "Carlos Rodriguez acoso verbal en pasillos"
    censurado, _, flagged = scan_pii(texto)
    assert flagged is True

