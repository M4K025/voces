"""Detección y censura de datos personales identificables (PII) en reportes.

Patrones detectados (regex):
  - correos electrónicos
  - teléfonos (formato colombiano, móvil y fijo)
  - códigos estudiantiles / cédulas (secuencias numéricas de 8 a 10 dígitos)
  - nombres propios probables (dos o más palabras con mayúscula inicial)

Se censura sustituyendo el hallazgo por una etiqueta clara ([EMAIL OMITIDO], etc.)
y se devuelve una bandera pii_flagged cuando se detectan nombres probables, para
que el panel de moderación revise el reporte. Nunca se rechazan reportes por PII
a menos que el texto quede vacío tras la censura.
"""

from __future__ import annotations

import re
from typing import Tuple

# Correo electrónico.
RE_EMAIL = re.compile(r"[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}")

# Teléfono colombiano: móvil 3XX XXX XX XX / +57 300..., fijo 7 u 8 dígitos con código de área.
RE_PHONE = re.compile(
    r"(\+57\s*)?(3[0-9]{2}[\s\-\.]?[0-9]{3}[\s\-\.]?[0-9]{2}[\s\-\.]?[0-9]{2}|"
    r"[0-9]{3}[\s\-\.]?[0-9]{3}[\s\-\.]?[0-9]{4}|"
    r"[0-9]{7,8})"
)

# Código estudiantil o cédula: secuencia aislada de 8 a 10 dígitos.
RE_CODE = re.compile(r"\b[0-9]{8,10}\b")

# Nombre propio probable: dos o más palabras con mayúscula inicial (con tildes/ñ).
RE_NAME = re.compile(
    r"\b[A-ZÁÉÍÓÚÑ][a-záéíóúñ]+\s+[A-ZÁÉÍÓÚÑ][a-záéíóúñ]+"
    r"(?:\s+[A-ZÁÉÍÓÚÑ][a-záéíóúñ]+)*"
)

_REPLACEMENTS = {
    "email": "[EMAIL OMITIDO]",
    "phone": "[TELÉFONO OMITIDO]",
    "code": "[CÓDIGO OMITIDO]",
    "name": "[NOMBRE OMITIDO]",
}


def scan_pii(text: str) -> Tuple[str, int, bool]:
    """Detecta y censura PII.

    Returns
    -------
    (censored_text, findings_count, pii_flagged)
        * pii_flagged es True si se detectó al menos un nombre propio probable,
          señal para el moderador.
    """
    if not text:
        return "", 0, False

    findings = 0
    pii_flagged = False
    result = text

    def replace(match: re.Match, tag: str) -> str:
        nonlocal findings
        findings += 1
        return _REPLACEMENTS[tag]

    result = RE_EMAIL.sub(lambda m: replace(m, "email"), result)
    result = RE_CODE.sub(lambda m: replace(m, "code"), result)
    result = RE_PHONE.sub(lambda m: replace(m, "phone"), result)

    def name_repl(match: re.Match) -> str:
        nonlocal findings, pii_flagged
        findings += 1
        pii_flagged = True
        return _REPLACEMENTS["name"]

    result = RE_NAME.sub(name_repl, result)

    return result, findings, pii_flagged


def looks_like_accusation(text: str) -> bool:
    """Heurística ligera: texto que acusa directamente a una persona nombrada."""
    lowered = text.lower()
    markers = ["funa", "expón", "expon", "denuncio a", "acuso a", "responsable es"]
    return any(m in lowered for m in markers)
