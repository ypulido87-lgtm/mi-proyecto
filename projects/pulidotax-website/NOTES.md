# Sitio web — Pulido Tax & Accounting LLC

**Estado:** En vivo en [pulidotax.com](https://pulidotax.com). Servido como HTML estático desde `public_html` en GoDaddy cPanel (WordPress instalado pero bypaseado con `DirectoryIndex index.html index.php`).

## Origen de verdad (movido aquí el 3 sep 2026)
Antes vivía en `C:\Users\yudit\Downloads\`. Ahora todo el proyecto está aquí:

- **`sitio-pulidotax/`** — las páginas que realmente se suben al servidor: `index.html`, `servicios.html`, `sobre-mi.html`, `blog.html`, `contacto.html`, favicons y `yudit-pulido.png`. Esta es la carpeta que se sube a GoDaddy.
- **`borradores-trabajo/`** — versiones de trabajo antiguas con la foto incrustada en base64 (`home.html`, `servicios.html`, `sobre-mi.html`, `contacto.html`, `blog.html`). Se guardan como referencia; nunca volver a incrustar base64 en producción (el server daba 404 con HTML >2 MB).
- **`google-business-profile/`** — logo (1080×1080) y portada (1200×675) generados para el perfil de Google Business.
- **`briefing_pulidotax_claudecode.txt`** — el briefing original del proyecto.
- **`borrador-antiguo-home.html`** — un borrador temprano ya superado (18 jun 2026), solo referencia histórica.
- **`articulo-de-la-semana.md`** — red de seguridad de la tarea automática: aparece aquí cuando hay un artículo escrito pero aún no insertado en `blog.html`.

## Automatización del blog
Dos tareas programadas (Claude Code scheduled tasks) mantienen el blog al día — **ya actualizadas para apuntar a esta carpeta** en vez de Downloads:
- `articulo-semanal-blog-pulidotax` — lunes 9 AM, escribe el artículo de la semana.
- `verificar-blog-pulidotax` — martes y jueves 10 AM, vigilante que rellena si falta.

Editan `sitio-pulidotax\blog.html` directamente y copian el resultado a `borradores-trabajo\blog.html`. Yudit sigue subiendo el archivo a GoDaddy manualmente (File Manager → Upload → sobre `sitio-pulidotax\blog.html` → "Overwrite existing files" marcada).

## Más contexto
Memoria completa del proyecto (reglas de la dueña, historial, causa de fallos pasados, formulario de contacto, Google Business Profile): `project_website_pulido_tax.md` en la memoria de Claude.
