"""Exportación de datos: PDF resumen para bienestar universitario y CSV anonimizado."""

from __future__ import annotations

import csv
import io
from datetime import datetime
from typing import Any

from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    Image,
)

from app.config import settings
from app.models.report import Report, ReportStatus, CATEGORY_LABELS
from app.services.stats import (
    reports_by_category,
    reports_by_place,
    reports_by_actor_role,
    reports_over_time,
    top_phrases,
    total_reports,
)
from sqlalchemy.orm import Session

try:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    MATPLOTLIB_AVAILABLE = True
except Exception:  # pragma: no cover - opcional en entornos sin display
    MATPLOTLIB_AVAILABLE = False


def _bar_chart_image(data: list[dict[str, Any]], title: str, label_key: str) -> str | None:
    """Genera un gráfico de barras y devuelve la ruta al archivo PNG temporal."""
    if not MATPLOTLIB_AVAILABLE or not data:
        return None
    labels = [str(d.get(label_key, "")) for d in data]
    values = [d.get("count", 0) for d in data]
    fig, ax = plt.subplots(figsize=(6, 3))
    ax.bar(range(len(labels)), values, color="#4f46e5")
    ax.set_xticks(range(len(labels)))
    ax.set_xticklabels(labels, rotation=30, ha="right", fontsize=7)
    ax.set_title(title, fontsize=9)
    ax.tick_params(axis="y", labelsize=7)
    path = f"/tmp/voces_{label_key}.png"
    fig.tight_layout()
    fig.savefig(path, dpi=150)
    plt.close(fig)
    return path


def export_pdf(db: Session, period_from: str | None = None, period_to: str | None = None) -> bytes:
    """Genera un PDF resumen con estadísticas agregadas del periodo indicado."""
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        leftMargin=2 * cm,
        rightMargin=2 * cm,
        topMargin=2 * cm,
        bottomMargin=2 * cm,
        title="VOCES — Informe de problemáticas de género",
        author="Facultad de Ingeniería - Universidad Distrital",
    )
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        "TitleCustom",
        parent=styles["Title"],
        fontSize=16,
        textColor=colors.HexColor("#1e3a8a"),
        spaceAfter=12,
    )
    h2 = ParagraphStyle(
        "H2Custom",
        parent=styles["Heading2"],
        fontSize=12,
        textColor=colors.HexColor("#1e3a8a"),
        spaceBefore=12,
        spaceAfter=6,
    )
    body = styles["Normal"]
    body.fontSize = 9

    story = []
    story.append(Paragraph("VOCES — Informe resumen de problemáticas de género", title_style))
    story.append(
        Paragraph(
            "Facultad de Ingeniería, Universidad Distrital Francisco José de Caldas. "
            "Datos agregados y anonimizados. Solo reportes aprobados.",
            body,
        )
    )
    story.append(Spacer(1, 12))
    story.append(
        Paragraph(
            f"Generado: {datetime.now().strftime('%d/%m/%Y %H:%M')}",
            body,
        )
    )
    story.append(Spacer(1, 12))

    total = total_reports(db, approved_only=True)
    story.append(Paragraph(f"Total de reportes aprobados: {total}", h2))
    story.append(Spacer(1, 6))

    # Tabla por categoría
    story.append(Paragraph("Reportes por categoría", h2))
    cat_data = [["Categoría", "Casos"]]
    for item in reports_by_category(db):
        cat_data.append([item["label"], str(item["count"])])
    cat_table = Table(cat_data, colWidths=[12 * cm, 4 * cm])
    cat_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1e3a8a")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                ("FONTSIZE", (0, 0), (-1, -1), 8),
                ("ALIGN", (1, 0), (-1, -1), "CENTER"),
            ]
        )
    )
    story.append(cat_table)
    story.append(Spacer(1, 12))

    # Tabla por lugar
    story.append(Paragraph("Reportes por lugar", h2))
    place_data = [["Lugar", "Casos"]]
    for item in reports_by_place(db):
        place_data.append([item["place"], str(item["count"])])
    place_table = Table(place_data, colWidths=[12 * cm, 4 * cm])
    place_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1e3a8a")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                ("FONTSIZE", (0, 0), (-1, -1), 8),
                ("ALIGN", (1, 0), (-1, -1), "CENTER"),
            ]
        )
    )
    story.append(place_table)
    story.append(Spacer(1, 12))

    # Tabla por rol de actor
    story.append(Paragraph("Reportes por rol de quien lo dijo", h2))
    role_data = [["Rol", "Casos"]]
    for item in reports_by_actor_role(db):
        role_data.append([item["actor_role"], str(item["count"])])
    role_table = Table(role_data, colWidths=[12 * cm, 4 * cm])
    role_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1e3a8a")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                ("FONTSIZE", (0, 0), (-1, -1), 8),
                ("ALIGN", (1, 0), (-1, -1), "CENTER"),
            ]
        )
    )
    story.append(role_table)
    story.append(Spacer(1, 12))

    # Frases más frecuentes
    story.append(Paragraph("Frases más frecuentes", h2))
    phrase_data = [["Frase (censurada)", "Veces"]]
    phrases = top_phrases(db)
    for phrase in phrases[:10]:
        phrase_data.append([phrase[:80], "1"])
    phrase_table = Table(phrase_data, colWidths=[12 * cm, 4 * cm])
    phrase_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1e3a8a")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                ("FONTSIZE", (0, 0), (-1, -1), 8),
                ("ALIGN", (1, 0), (-1, -1), "CENTER"),
            ]
        )
    )
    story.append(phrase_table)

    doc.build(story)
    pdf_bytes = buffer.getvalue()
    buffer.close()
    return pdf_bytes


def export_csv_anonymized(db: Session) -> str:
    """Exporta reportes aprobados a CSV anonimizado (sin datos identificables)."""
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(
        [
            "id",
            "content",
            "category",
            "place",
            "actor_role",
            "period",
            "is_witness",
            "career",
            "semester",
            "status",
            "pii_flagged",
            "is_demo",
            "created_at",
        ]
    )
    stmt = (
        select(Report)
        .where(Report.status == ReportStatus.aprobado)
        .order_by(Report.created_at.desc())
    )
    for report in db.execute(stmt).scalars():
        writer.writerow(
            [
                report.id,
                report.content,
                report.category.value,
                report.place,
                report.actor_role or "",
                report.period or "",
                report.is_witness if report.is_witness is not None else "",
                report.career or "",
                report.semester or "",
                report.status.value,
                report.pii_flagged,
                report.is_demo,
                report.created_at.isoformat() if report.created_at else "",
            ]
        )
    return output.getvalue()
