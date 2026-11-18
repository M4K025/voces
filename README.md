# VOCES — Visibilización de problemáticas de género

**Facultad de Ingeniería, Universidad Distrital Francisco José de Caldas (Bogotá)**

Aplicación web para recoger, de forma anónima, frases, comentarios y situaciones
"fuera de lugar" relacionadas con género (machismo, comentarios sexistas,
microagresiones, acoso, discriminación, exclusión en trabajos grupales, etc.).
El objetivo es hacer visible el problema con datos, sensibilizar y orientar hacia
canales de apoyo. **No es una herramienta para exponer, acusar ni "funar" a
personas individuales.**

---

## Stack

- **Backend:** Python 3.11+ con FastAPI
- **Base de datos:** SQLite con SQLAlchemy 2.0
- **Frontend:** HTML + Jinja2 + Tailwind CSS (CDN) + Chart.js, responsive, móvil primero
- **Tests:** pytest
- **Exportación:** PDF (reportlab) y CSV anonimizado

---

## Requisitos

- Python 3.11+ (se probó con 3.15)
- `pip` para instalar dependencias

---

## Instalación y ejecución

```bash
# 1. Clonar o descomprimir el proyecto
cd proyecto-generos

# 2. Instalar dependencias
pip install -r requirements.txt

# 3. Definir la contraseña de administración (obligatoria, nunca se hardcodea)
# PowerShell:
$env:VOCES_ADMIN_PASSWORD="TuContraseñaSegura123"

# CMD:
set VOCES_ADMIN_PASSWORD=TuContraseñaSegura123

# Linux/macOS:
export VOCES_ADMIN_PASSWORD=TuContraseñaSegura123

# 4. Ejecutar la aplicación
uvicorn app.main:app

# Nota: si el comando `uvicorn` apunta a otra versión de Python, usa:
python -m uvicorn app.main:app
```

La aplicación quedará disponible en `http://127.0.0.1:8000`.

---

## Variables de entorno

| Variable | Descripción | Obligatoria | Valor por defecto |
|---|---|---|---|
| `VOCES_ADMIN_PASSWORD` | Contraseña del panel de administración (hash bcrypt) | **Sí** | — |
| `VOCES_SECRET_KEY` | Clave para firmar sesiones y cookies | No | `dev-insecure-secret-key-change-me` |
| `VOCES_ADMIN_USERNAME` | Usuario de administración | No | `admin` |
| `VOCES_DATABASE_URL` | URL de la base de datos | No | `sqlite:///./voces.db` |
| `VOCES_SESSION_COOKIE_NAME` | Nombre de la cookie de sesión | No | `voces_session` |
| `VOCES_SESSION_MAX_AGE` | Duración de la sesión (segundos) | No | `3600` |
| `VOCES_RATE_LIMIT_REQUESTS` | Máx. peticiones por ventana de rate limit | No | `20` |
| `VOCES_RATE_LIMIT_WINDOW` | Ventana del rate limit (segundos) | No | `60` |
| `VOCES_DASHBOARD_MIN_GROUP` | Mínimo de casos por grupo para mostrar datos (evita re-identificación) | No | `5` |
| `VOCES_DEBUG` | Modo desarrollo (`true`/`false`) | No | `false` |

---

## Funcionalidades

1. **Formulario de reporte anónimo** (sin login)
   - Texto libre (máx. 500 caracteres), categoría, lugar, rol de quien lo dijo, fecha aproximada, testigo/víctima, carrera/semestre opcionales.
   - Nunca se piden nombres propios.

2. **Privacidad por diseño**
   - No se guardan IP, correos ni cookies de seguimiento.
   - Rate limit con hash de IP y **sal rotativa no persistida** (la IP no se reconstruye).
   - Detección automática (regex) de nombres propios, correos, teléfonos y códigos estudiantiles: se censuran o se marca el reporte para revisión de moderación.
   - Aviso de privacidad visible alineado con la **Ley 1581 de 2012 (Habeas Data, Colombia)**.

3. **Cola de moderación**
   - Todo reporte entra como "pendiente".
   - Panel de administración con login (usuario/contraseña con hash bcrypt, sesión firmada y expirable).
   - Acciones: aprobar, editar (censurar datos identificables) o rechazar.
   - Solo los aprobados se muestran públicamente.

4. **Muro público "Lo que se escucha"**
   - Lista paginada de reportes aprobados con filtros por categoría, lugar y semestre.
   - Botón "a mí también me pasó" (contador anónimo, un voto por dispositivo sin rastreo invasivo).

5. **Dashboard de datos agregados** (panel de admin)
   - Total de reportes, por categoría, por lugar, por rol de quien lo dijo, evolución por mes/semestre, frases más frecuentes.
   - **Umbral mínimo:** grupos con menos de 5 casos se ocultan para evitar re-identificación.

6. **"¿Por qué es problemático?"**
   - Explicación pedagógica breve por categoría y sugerencias de intervención de espectador.

7. **Directorio de apoyo**
   - Rutas de atención administrables desde el panel.
   - Datos de ejemplo marcados claramente como **"PLACEHOLDER, verificar"**. No se inventan teléfonos ni correos reales.

8. **Reporte exportable** (panel de admin)
   - PDF resumen con gráficas y estadísticas por periodo, para entregar a bienestar universitario o decanatura.
   - CSV anonimizado de reportes aprobados.

9. **Encuesta corta de percepción** (8 preguntas, escala 1-5)
   - Resultados agregados en el dashboard.

### Funcionalidades extra incluidas

- Modo claro/oscuro (persistente en `localStorage`) y accesibilidad básica (enlace "Saltar al contenido", etiquetas ARIA, contraste).
- Mensaje de apoyo inmediato tras enviar un reporte, con recursos de la sección de apoyo.
- Interfaz en español con lenguaje inclusivo y tono respetuoso.

---

## Seguridad

- Protección contra XSS: Jinja2 con autoescape; todo texto de usuario se escapa al renderizar.
- Protección contra CSRF: token por sesión en formularios que modifican estado.
- Inyección SQL: SQLAlchemy ORM con consultas parametrizadas.
- Contraseña de admin con hash bcrypt, únicamente por variable de entorno.
- No se almacenan IPs, correos ni cookies de seguimiento.

---

## Datos semilla (demo)

Al iniciar la aplicación, se siembran automáticamente datos **ficticios** marcados con `is_demo = True`:
- 15 reportes aprobados distribuidos en categorías y lugares.
- 12 respuestas de encuesta de percepción.
- Recursos de apoyo marcados como PLACEHOLDER.
- Usuario de administrador `admin` (contraseña = `VOCES_ADMIN_PASSWORD`).

Estos datos sirven para demostrar el dashboard y no representan reportes reales.

---

## Pruebas

```bash
pip install -r requirements.txt
python -m pytest tests/ -v
```

Los tests cubren:
- Validación del formulario de reporte (campos obligatorios, largo máximo, CSRF).
- Censura de datos personales (correos, teléfonos, códigos, nombres propios).
- Moderación (aprobar, rechazar, editar con censura de PII).
- Umbral mínimo del dashboard (grupos con menos de 5 casos se ocultan).

---

## Despliegue

1. Definir `VOCES_ADMIN_PASSWORD` con una contraseña segura.
2. Definir `VOCES_SECRET_KEY` con una clave aleatoria y secreta.
3. En producción, establecer `VOCES_DEBUG=false` y restringir `TrustedHostMiddleware` a los hosts reales.
4. Ejecutar con un servidor ASGI de producción (uvicorn, gunicorn + uvicorn workers).
5. Considerar usar una base de datos PostgreSQL/MySQL en lugar de SQLite para entornos con concurrencia.

---

## Estructura del proyecto

```
voces/
├── app/
│   ├── __init__.py
│   ├── config.py              # Configuración por variables de entorno
│   ├── database.py            # SQLAlchemy engine, sesión, init_db
│   ├── dependencies.py        # Plantillas Jinja2, CSRF, auth
│   ├── main.py                # App FastAPI, middleware, lifespan, routers
│   ├── models/                # Modelos SQLAlchemy (reporte, admin, encuesta, apoyo, etc.)
│   ├── routers/               # Rutas públicas, administración, semilla
│   ├── services/              # PII, rate limit, auth, stats, exportación
│   ├── static/css/app.css     # Estilos complementarios
│   └── templates/             # Plantillas Jinja2 (base, muro, reporte, admin, etc.)
├── tests/                     # Tests de pytest
├── requirements.txt
├── README.md
└── ROADMAP.md
```

---

## Licencia

Uso interno académico — Facultad de Ingeniería, Universidad Distrital Francisco José de Caldas.
