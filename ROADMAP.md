# ROADMAP — VOCES

Mejoras planificadas para versiones futuras, en orden de prioridad sugerido.

## Corto plazo (1–3 meses)

- [ ] **Sección dedicada "Cómo actuar si presencias una situación"**: guía paso a paso de intervención de espectador, independiente de las categorías.
- [ ] **Mensaje de apoyo inmediato más completo**: mostrar recursos específicos según la categoría del reporte.
- [ ] **Exportar datos anonimizados a CSV**: ya implementado; añadir filtro por rango de fechas.
- [ ] **Tests de exportación (PDF/CSV)**: validar contenido generado.
- [ ] **Tests de frontend (Playwright/Cypress)**: pruebas de navegación y flujos clave.
- [ ] **Validación más estricta de PII**: reducir falsos positivos en detección de nombres/códigos.
- [ ] **Notificación por correo al moderador** cuando hay reportes pendientes (opcional, configurado por env).

## Medio plazo (3–6 meses)

- [ ] **Autenticación multifactor (MFA)** para el panel de administración.
- [ ] **Registro de auditoría de moderación**: quién aprobó/rechazó cada reporte y cuándo (sin datos del denunciante).
- [ ] **API REST pública** para consultar estadísticas agregadas (con autenticación por token).
- [ ] **Dashboard público opcional**: visualización agregada sin necesidad de login de admin.
- [ ] **Envío de reportes por WhatsApp/SMS** como canal alternativo (sin guardar el número).
- [ ] **Mapa de calor interactivo** por lugar (más allá de barras estáticas).
- [ ] **Análisis de sentimiento y nube de palabras** de frases aprobadas (procesamiento local de lenguaje natural).
- [ ] **Internacionalización (i18n)**: inglés e idiomas indígenas de Colombia.

## Largo plazo (6–12 meses)

- [ ] **Migración de SQLite a PostgreSQL/MySQL** para soporte de concurrencia y múltiples instancias.
- [ ] **Despliegue con Docker** y docker-compose.
- [ ] **Integración con sistemas institucionales** de bienestar universitario (SSO, LDAP de la universidad).
- [ ] **Chatbot de orientación** con respuestas predefinidas y derivación a canales humanos.
- [ ] **Sistema de tickets** para seguimiento de casos derivados a bienestar (sin identificar al denunciante).
- [ ] **Análisis de tendencias temporales** con alertas automáticas ante picos de reportes.
- [ ] **Auditoría de seguridad externa** y pruebas de penetración.

## Diseño y experiencia

- [ ] **Accesibilidad WCAG 2.1 AA**: navegación por teclado completa, contraste mejorado, lectores de pantalla.
- [ ] **Modo lectora** y tamaños de fuente ajustables.
- [ ] **PWA (Progressive Web App)** para uso sin instalación desde el celular.
- [ ] **Notificaciones push** (opcional, sin identificar al usuario).

## Gobernanza y datos

- [ ] **Protocolo de retención de datos**: borrado automático de reportes antiguos (ej. > 2 años) salvo que se requiera para estadísticas.
- [ ] **Comité de gobernanza de datos**: revisión periódica de anonimización y umbrales de re-identificación.
- [ ] **Informe anual automatizado** para la decanatura y bienestar universitario.

---

*Nota: cualquier dato de ejemplo (teléfonos, correos, nombres de instancia) en el directorio de apoyo está marcado como "PLACEHOLDER, verificar" y debe confirmarse con fuentes oficiales antes de un despliegue real.*
