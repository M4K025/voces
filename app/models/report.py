"""Modelo de reporte anónimo y enumeraciones relacionadas."""

from __future__ import annotations

from datetime import datetime
from enum import Enum as PyEnum
from typing import Optional

from sqlalchemy import (
    Boolean,
    DateTime,
    Enum,
    Integer,
    String,
    Text,
    func,
    select,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class ReportStatus(PyEnum):
    pendiente = "pendiente"
    aprobado = "aprobado"
    rechazado = "rechazado"


class ReportCategory(PyEnum):
    comentario_sexista = "comentario_sexista"
    microagresion = "microagresion"
    acoso_verbal = "acoso_verbal"
    acoso_fisico = "acoso_fisico"
    discriminacion_academica = "discriminacion_academica"
    exclusion_grupo = "exclusion_grupo"
    comentario_docente = "comentario_docente"
    burla_orientacion = "burla_orientacion"
    otro = "otro"


# Etiquetas legibles para categorías (español, tono respetuoso e inclusivo)
CATEGORY_LABELS = {
    ReportCategory.comentario_sexista: "Comentario sexista",
    ReportCategory.microagresion: "Microagresión",
    ReportCategory.acoso_verbal: "Acoso verbal",
    ReportCategory.acoso_fisico: "Acoso físico",
    ReportCategory.discriminacion_academica: "Discriminación académica",
    ReportCategory.exclusion_grupo: "Exclusión en trabajo en grupo",
    ReportCategory.comentario_docente: "Comentario de docente",
    ReportCategory.burla_orientacion: "Burla por orientación o identidad",
    ReportCategory.otro: "Otro",
}

# Etiquetas pedagógicas breves ("¿por qué es problemático?")
CATEGORY_EXPLANATIONS = {
    ReportCategory.comentario_sexista: (
        "Refuerzan estereotipos de género y naturalizan la desigualdad entre hombres y mujeres, "
        "creando un clima hostil en el salón o laboratorio."
    ),
    ReportCategory.microagresion: (
        "Comentarios sutiles, a menudo presentados como 'broma', que desestiman capacidades o "
        "experiencias de una persona por su género. Aíslan y generan desconfianza acumulativa."
    ),
    ReportCategory.acoso_verbal: (
        "Palabras ofensivas, insinuaciones o amenazas que vulneran la dignidad y el derecho a un "
        "entorno educativo libre de violencia."
    ),
    ReportCategory.acoso_fisico: (
        "Contacto físico no consentido o acercamientos que intimidan. Constituye una violación grave "
        "del espacio personal y debe canalizarse por vías de protección universitaria."
    ),
    ReportCategory.discriminacion_academica: (
        "Trato desigual en notas, oportunidades o participación por razones de género, lo que afecta "
        "el rendimiento académico y la trayectoria estudiantil."
    ),
    ReportCategory.exclusion_grupo: (
        "Dejar fuera de trabajos en grupo o de decisiones por el género de la persona. Limita el "
        "aprendizaje colaborativo y refuerza la exclusión."
    ),
    ReportCategory.comentario_docente: (
        "Comentarios de docentes que estereotipan o menosprecian por género. Al provenir de una figura "
        "de autoridad, el impacto en el clima de clase es mayor."
    ),
    ReportCategory.burla_orientacion: (
        "Mofas o comentarios despectivos por orientación sexual o identidad de género. Atentan contra "
        "el derecho a la identidad y a un entorno libre de discriminación."
    ),
    ReportCategory.otro: (
        "Otra situación relacionada con género no cubierta por las categorías anteriores."
    ),
}

# Sugerencias de intervención de espectador ("qué decir o hacer como testigo")
CATEGORY_BYSTANDER_TIPS = {
    ReportCategory.comentario_sexista: (
        "Puedes decir: 'No me parece apropiado ese comentario' o cambiar el tema. Si es seguro, "
        "apoya a la persona afectada y deriva a canales de bienestar."
    ),
    ReportCategory.microagresion: (
        "Pregunta con calma: '¿qué quisiste decir con eso?'. Visibiliza el efecto de la frase sin "
        "enfrentar de forma agresiva."
    ),
    ReportCategory.acoso_verbal: (
        "Interrumpe si puedes: 'Eso es irrespetuoso'. Acompaña a la persona afectada y anima a reportar."
    ),
    ReportCategory.acoso_fisico: (
        "Prioriza la seguridad. No intervengas físicamente si te pone en riesgo; busca ayuda inmediata "
        "de seguridad universitaria o bienestar."
    ),
    ReportCategory.discriminacion_academica: (
        "Si notas trato desigual en clase, comenta con el docente desde el respeto o acude a la "
        "decanatura/facultad."
    ),
    ReportCategory.exclusion_grupo: (
        "Invita activamente a la persona excluida a participar y asegura que sus ideas se escuchen."
    ),
    ReportCategory.comentario_docente: (
        "Si te sientes seguro, habla con el docente en privado o canaliza a través del representante "
        "estudiantil o bienestar universitario."
    ),
    ReportCategory.burla_orientacion: (
        "Afirma que el respeto es ineludible en la facultad. Muestra solidaridad con la persona blanco "
        "de la burla y deriva a canales de apoyo."
    ),
    ReportCategory.otro: (
        "Escucha sin juzgar, valida la experiencia de la persona y orienta hacia los canales de apoyo."
    ),
}


class Report(Base):
    __tablename__ = "reports"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    # Texto ya censurado (datos personales removidos). Se guarda solo lo necesario.
    content: Mapped[str] = mapped_column(Text, nullable=False)
    category: Mapped[ReportCategory] = mapped_column(Enum(ReportCategory), nullable=False, index=True)
    place: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    actor_role: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    period: Mapped[Optional[str]] = mapped_column(String(50), nullable=True, index=True)  # mes / semestre
    is_witness: Mapped[Optional[bool]] = mapped_column(Boolean, nullable=True)
    career: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    semester: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    status: Mapped[ReportStatus] = mapped_column(
        Enum(ReportStatus), default=ReportStatus.pendiente, nullable=False, index=True
    )
    # Señal de posible dato identificable restante (no se guarda el dato en sí).
    pii_flagged: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_demo: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    moderator_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False
    )
    updated_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime, onupdate=func.now(), nullable=True
    )

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "content": self.content,
            "category": self.category.value,
            "category_label": CATEGORY_LABELS.get(self.category, self.category.value),
            "place": self.place,
            "actor_role": self.actor_role,
            "period": self.period,
            "is_witness": self.is_witness,
            "career": self.career,
            "semester": self.semester,
            "status": self.status.value,
            "pii_flagged": self.pii_flagged,
            "is_demo": self.is_demo,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
