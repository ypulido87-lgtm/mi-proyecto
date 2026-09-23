# Pulido Tax Editor (skill)

Skill editorial profesional para el blog de Pulido Tax & Accounting LLC. Instalado el 23 sep 2026 (Yudit lo trajo ya armado, no lo creamos en esta conversación).

## Qué hace (y qué NO hace)
Este skill gobierna **qué escribir y cómo redactarlo** — no reemplaza el flujo de publicación técnica que ya tenemos:

- **5 pilares de contenido** (no solo noticias del IRS): Taxes, Tax Credits, Accounting & Bookkeeping, Payroll, Small Business.
- Investiga desarrollos de ~7 días, verifica en fuentes primarias (`references/trusted-sources.md`), evita repetir temas ya cubiertos (`references/published-articles.md`), nunca fabrica cifras/fechas/citas.
- Produce el artículo en español (y opcionalmente inglés) con metadatos SEO — pero **no** lo inserta en `blog.html` ni lo sube a GoDaddy. Eso lo seguimos haciendo con el flujo ya establecido: escribir a `articulo-de-la-semana.md`, insertar card+modal en `sitio-pulidotax\blog.html`, subir vía API de cPanel, actualizar `blog.md`, commit/push.

## Instalación
- Fuente en `C:\Claude\projects\pulido-tax-editor\` (SKILL.md + references\, aplanado del zip original que traía doble carpeta).
- Copiado a `C:\Users\yudit\.claude\skills\pulido-tax-editor\` para que esté disponible como skill en cualquier sesión — confirmado activo de inmediato (apareció en la lista de skills disponibles sin reiniciar).

## Registro de artículos publicados
`references/published-articles.md` venía vacío (solo la plantilla). Lo llené con los **18 artículos** ya publicados en pulidotax.com/blog.html (12 ene – 23 sep 2026), para que la detección de duplicados funcione de verdad desde ya. Falta: Title EN y Main official source de la mayoría (no se registraron en su momento — no se inventaron, se dejaron en blanco a propósito).

## Cómo usarlo en la práctica
Cuando toque el artículo de la semana: seguir el flujo Monday workflow de este skill para investigar y redactar (da mejores resultados que solo "1 búsqueda web" que usaba la tarea programada vieja), y luego aplicar el mismo proceso técnico de inserción/publicación que ya usamos manualmente. Después de publicar, agregar la entrada correspondiente a `published-articles.md` con Status: Published — en ambas copias (skill instalado y esta carpeta fuente) para no perder sincronía.
