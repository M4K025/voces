"""Siembra de datos de demostración (demo) al arrancar la aplicación.

Todos los registros creados aquí llevan is_demo=True y están claramente
marcados como datos ficticios para demostrar el dashboard. No son reportes
reales de personas.
"""

from __future__ import annotations

from sqlalchemy.orm import Session

from app.models import (
    Report,
    ReportStatus,
    ReportCategory,
    AdminUser,
    SupportResource,
    CategoryInfo,
    Place,
    PerceptionResponse,
)
from app.services.auth import get_password_hash


SEED_ADMIN_USERNAME = "admin"


def _already_seeded(db: Session) -> bool:
    return db.query(Report).filter(Report.is_demo == True).first() is not None  # noqa: E712


def seed_demo_data(db: Session) -> None:
    if _already_seeded(db):
        return

    # --- Usuario de admin demo (la contraseña real debe venir del env; aquí solo si no existe) ---
    if not db.query(AdminUser).filter(AdminUser.username == SEED_ADMIN_USERNAME).first():
        import os

        demo_password = os.getenv("VOCES_ADMIN_PASSWORD", "VocesDemo2024!")
        db.add(
            AdminUser(
                username=SEED_ADMIN_USERNAME,
                password_hash=get_password_hash(demo_password),
                is_active=True,
            )
        )

    # --- Lugares ---
    places = [
        Place(key="salon", name="Salón de clases", order_index=1),
        Place(key="laboratorio", name="Laboratorio", order_index=2),
        Place(key="cafeteria", name="Cafetería", order_index=3),
        Place(key="pasillos", name="Pasillos", order_index=4),
        Place(key="canchas", name="Canchas", order_index=5),
        Place(key="virtual", name="Virtual / chat", order_index=6),
        Place(key="otro", name="Otro", order_index=7),
    ]
    for p in places:
        db.add(p)

    # --- Categorías pedagógicas ---
    from app.models.report import CATEGORY_EXPLANATIONS, CATEGORY_BYSTANDER_TIPS, CATEGORY_LABELS

    cat_order = {
        ReportCategory.comentario_sexista: 1,
        ReportCategory.microagresion: 2,
        ReportCategory.acoso_verbal: 3,
        ReportCategory.acoso_fisico: 4,
        ReportCategory.discriminacion_academica: 5,
        ReportCategory.exclusion_grupo: 6,
        ReportCategory.comentario_docente: 7,
        ReportCategory.burla_orientacion: 8,
        ReportCategory.otro: 9,
    }
    for cat_name, enum_member in ReportCategory.__members__.items():
        enum_cat = ReportCategory(cat_name)
        db.add(
            CategoryInfo(
                key=enum_cat.value,
                name=CATEGORY_LABELS.get(enum_cat, cat_name),
                explanation=CATEGORY_EXPLANATIONS.get(enum_cat, ""),
                bystander_tip=CATEGORY_BYSTANDER_TIPS.get(enum_cat, ""),
                order_index=cat_order.get(enum_cat, 99),
            )
        )

    # --- Reportes demo (aprobados) para el dashboard ---
    demo_reports = [
        ("Me dijeron que las mujeres no sirven para la ingeniería", ReportCategory.comentario_sexista, "salon", "estudiante", "2024-1", True, "Ingeniería de Sistemas", "4"),
        ("Una compañera fue excluida del proyecto por ser mujer", ReportCategory.exclusion_grupo, "salon", "estudiante", "2024-1", True, "Ingeniería Civil", "5"),
        ("Docente hizo un comentario sexista en clase", ReportCategory.comentario_docente, "salon", "docente", "2024-1", False, None, None),
        ("Comentario sobre la apariencia de una compañera en el laboratorio", ReportCategory.microagresion, "laboratorio", "estudiante", "2024-1", True, "Ingeniería Electrónica", "3"),
        ("Me sentí incómodo con un acercamiento físico no deseado", ReportCategory.acoso_fisico, "pasillos", "externo", "2024-1", True, None, None),
        ("Burlas por orientación sexual en el chat del curso", ReportCategory.burla_orientacion, "virtual", "estudiante", "2024-2", False, "Ingeniería de Sistemas", "2"),
        ("Trato desigual en notas por género", ReportCategory.discriminacion_academica, "salon", "docente", "2024-2", True, "Ingeniería Mecánica", "6"),
        ("Acoso verbal en la cafetería", ReportCategory.acoso_verbal, "cafeteria", "estudiante", "2024-2", True, None, None),
        ("Excluidos del equipo por ser hombres", ReportCategory.exclusion_grupo, "laboratorio", "estudiante", "2024-2", True, "Ingeniería de Sistemas", "4"),
        ("Comentario denigrante de docente sobre mujeres en STEM", ReportCategory.comentario_docente, "salon", "docente", "2024-2", True, None, None),
        ("Otra situación de género en pasillos", ReportCategory.otro, "pasillos", "estudiante", "2024-2", False, None, None),
        ("Comentario sexista repetido en laboratorio", ReportCategory.comentario_sexista, "laboratorio", "estudiante", "2024-2", True, "Ingeniería Civil", "5"),
        ("Microagresión hacia compañera en grupo", ReportCategory.microagresion, "salon", "estudiante", "2024-1", True, None, None),
        ("Acoso físico en canchas", ReportCategory.acoso_fisico, "canchas", "externo", "2024-1", False, None, None),
        ("Burla por identidad de género", ReportCategory.burla_orientacion, "pasillos", "estudiante", "2024-2", True, None, None),
    ]
    for i, (content, category, place, actor_role, period, is_witness, career, semester) in enumerate(demo_reports):
        db.add(
            Report(
                content=content,
                category=category,
                place=place,
                actor_role=actor_role,
                period=period,
                is_witness=is_witness,
                career=career,
                semester=semester,
                status=ReportStatus.aprobado,
                pii_flagged=False,
                is_demo=True,
            )
        )

    # --- Recursos de apoyo (PLACEHOLDER, verificar) ---
    resources = [
        SupportResource(
            title="Bienestar Universitario - Universidad Distrital",
            description="Atención psicológica y orientación para la comunidad universitaria (PLACEHOLDER, verificar datos).",
            resource_type="universidad",
            phone=None,
            email=None,
            url=None,
            is_placeholder=True,
            is_active=True,
            order_index=1,
        ),
        SupportResource(
            title="Línea 155 - Violencia de género (Colombia)",
            description="Línea gratuita nacional de orientación en casos de violencia de género (PLACEHOLDER, verificar).",
            resource_type="nacional",
            phone="155",
            email=None,
            url=None,
            is_placeholder=True,
            is_active=True,
            order_index=2,
        ),
    ]
    for r in resources:
        db.add(r)

    # --- Respuestas demo de encuesta de percepción ---
    for _ in range(12):
        db.add(
            PerceptionResponse(
                answers={
                    "q1": 3,
                    "q2": 4,
                    "q3": 2,
                    "q4": 3,
                    "q5": 2,
                    "q6": 4,
                    "q7": 3,
                    "q8": 3,
                },
                is_demo=True,
            )
        )

    db.commit()
