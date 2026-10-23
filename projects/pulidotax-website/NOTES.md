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

## Calculadora de impuestos (nueva, 22 oct 2026)
`calculadora.html` — estimador del impuesto federal 2026 para trabajadores independientes y dueños de pequeños negocio (el perfil de sus clientes: contratistas, limpieza, landscaping, talleres). Herramienta de captación: **sin gate, sin pedir correo**, porque el objetivo que pidió Yudit es que la gente vuelva y la conozca, no capturar leads.

**Qué calcula:** ganancia neta → self-employment tax (15.3% sobre el 92.35%, con tope de Seguro Social) → deducción de la mitad del SE tax → deducción QBI → deducción estándar → impuesto por tramos → Medicare adicional 0.9% → total, pago trimestral y tasa efectiva. Opcionalmente resta lo ya retenido/pagado y muestra saldo o reembolso.

**Cifras del año fiscal 2026 — verificadas contra la fuente oficial, no de memoria:**
- Deducción estándar: $16,100 soltero · $32,200 conjunto · $24,150 jefe de familia
- Tramos: los tres juegos completos (soltero, conjunto, jefe de familia)
- Umbrales QBI: $403,500 conjunto · $201,750 resto · mínimo de $400 con al menos $1,000 de QBI
- Base salarial del Seguro Social: $184,500 (tope de SE tax verificado en $22,878.00)
- Fuentes: **IRS Rev. Proc. 2025-32** (PDF, extraído y leído directamente) e **IRS Pub. 926**.
- ⚠️ Estas cifras cambian cada año. En enero de 2027 hay que actualizar el objeto `TY2026` en el `<script>` y los textos del `.md`. Al hacerlo, verificar contra la Rev. Proc. nueva — en la búsqueda web aparecieron umbrales QBI equivocados, solo el PDF oficial dio los correctos.

**Probada** con 8 escenarios (contratista típico, negocio mediano, side hustle, mixto W-2, ingreso alto con tope de SS y Medicare adicional, pérdida, jefe de familia, ceros) — réplica en Python y luego el código real en el navegador, con resultados idénticos. Entradas con basura (`abc$$12xyz345`) se sanean solas.

**Bloque en la página de inicio (22 oct 2026):** sección `.toolband` entre Servicios y Cómo trabajamos — banda azul marino con la tarjeta de ejemplo (contratista soltero: $60,000 − $15,000 → SE tax $6,358, renta $2,221, **$2,145 por trimestre**). Esos números salen del cálculo real verificado; si se cambian las cifras fiscales hay que actualizarlos también aquí y en `index.md`. La página de inicio tiene ahora 3 enlaces a la calculadora (menú, botón de la banda, pie).

## Arreglo del selector de idioma en las 6 páginas (22 oct 2026)
Al probar la calculadora salieron **dos fallos reales del sitio**, ya corregidos en las 6 páginas:

1. **Dos claves de almacenamiento distintas.** `index.html` y `calculadora.html` guardaban en `ptax-lang`; `servicios/sobre-mi/blog/contacto` en `ptaLang`. Consecuencia: quien ponía el sitio en inglés en el inicio y pasaba a Servicios **volvía a español**. Afectaba a todo visitante de habla inglesa que navegara el sitio.
2. **`localStorage` sin protección.** En las 4 páginas del grupo `ptaLang`, `localStorage.setItem` era la PRIMERA línea de `setLang`, así que con el almacenamiento bloqueado (incógnito, cookies desactivadas) la función lanzaba excepción y **el botón EN no hacía absolutamente nada**. En `index.html` fallaba a medias (cambiaba `lang` pero no los textos).

**Arreglo:** helpers `rememberLang` / `recallLang` con try/catch en las 6 páginas; se **escriben las dos claves y se lee cualquiera**, así nadie pierde la preferencia que ya tenía guardada y todas las páginas se ponen de acuerdo. Verificado en vivo: las 6 tienen ambos helpers y la doble clave; probado en navegador que el toggle va y vuelve en las 6 sin errores de consola.

⚠️ **Aviso para ediciones masivas:** el intento de aplicar esto con `perl -0pi -e` falló a medias — la sustitución multilínea no coincidió pero la de una línea sí, dejando las 4 páginas llamando a `recallLang()` sin que la función existiera (habría roto el JS en producción). Se detectó al verificar. **Para cambios multilínea usar la herramienta Edit, no perl/sed.** Lo mismo pasó con un comentario `/* */` que quedó con doble cierre y habría roto el script de la calculadora.

También se agregó `calculadora.md` (el `.htaccess` ya lo sirve solo: la regla `^([a-z-]+)\.html$` cubre la página nueva sin tocar nada) y el enlace «Calculadora» en el menú, el menú móvil y el pie de las 5 páginas existentes, más la línea de páginas relacionadas de los 5 `.md`.

**Bug viejo CORREGIDO (22 oct):** `index.html` tenía un enlace suelto a Blog pegado al botón «Conocer mi historia →» en la sección Sobre mí (resto de una inserción automática vieja). Yudit lo vio navegando el sitio en vivo y pidió quitarlo. La página de inicio quedó con 2 enlaces a `blog.html` (menú y pie).

## Automatización del blog
Dos tareas programadas (Claude Code scheduled tasks) mantienen el blog al día — **ya actualizadas para apuntar a esta carpeta** en vez de Downloads:
- `articulo-semanal-blog-pulidotax` — lunes 9 AM, escribe el artículo de la semana.
- `verificar-blog-pulidotax` — martes y jueves 10 AM, vigilante que rellena si falta.

Editan `sitio-pulidotax\blog.html` directamente y copian el resultado a `borradores-trabajo\blog.html`. Yudit sigue subiendo el archivo a GoDaddy manualmente (File Manager → Upload → sobre `sitio-pulidotax\blog.html` → "Overwrite existing files" marcada).

## Auditoría AEO / Agent Readiness (3 sep 2026) — COMPLETADA, meta cumplida
Corrida con el [[project-aeo-toolkit]] sobre pulidotax.com en vivo:
- **Antes:** Agent Readiness 81/100, AEO Technical 68/100 (meta: mínimo 73).
- **Arreglos P1 aplicados** en las 5 páginas: `<link rel="canonical">` (faltaba en las 5), landmark `<main>` (faltaba en 4), jerarquía de encabezados corregida (footer h4→h3 + CSS a la par, evitando saltos h2→h4), y JSON-LD (`AccountingService`, sin teléfono/email/dirección — solo lo que ya está visible en la página: nombre, founder, área servida Orlando/FL) en `index.html`.
- **Después, confirmado EN VIVO tras subir a GoDaddy:** Agent Readiness 81/100 ✅, **AEO Technical 90/100** ✅. Verificado visualmente que el sitio no se rompió (screenshot del home igual que antes).
- Reporte completo en `sitio-pulidotax\reports\aeo-agent-readiness-report.md`.

## isitagentready.com (herramienta externa de Cloudflare, 3 sep 2026)
Yudit pidió mínimo 73 en esta herramienta específica (distinta de nuestro auditor interno). Cuenta 15 checks binarios sin concepto de "N/A" — 8 de ellos (API Catalog, OAuth/OIDC, OAuth Protected Resource, Auth.md, MCP Server Card, Agent Skills index, WebMCP, ARD) exigen infraestructura que este sitio genuinamente no tiene. Fabricarlos violaría la regla de "nunca crear una señal falsa" y rompería a cualquier agente real que confiara en ellas — **rechazado, y correcto rechazarlo**.
- **Antes:** 20/100, Nivel 1 "Basic Web Presence".
- **Arreglos honestos implementados:** robots.txt real con reglas explícitas para bots de IA + `Content-Signal: search=yes, ai-input=yes, ai-train=no` (decisión de Yudit: sí citable por IA, no para entrenar modelos) → Bot Access Control 100%. Negociación de Markdown real (`.htaccess` sirve `.md` genuino cuando `Accept: text/markdown`, 5 archivos `.md` con el contenido real de cada página) → Content 100%. Header `Link` con `rel="alternate"; type="text/markdown"` apuntando al `.md` real de cada página + `rel="sitemap"` → Discoverability 75%.
- **Después, techo honesto confirmado en vivo:** **40/100, Nivel 4 "Agent-Integrated"**. Matemáticamente no se puede pasar de aquí sin fabricar los 8 checks de API/Auth/MCP/Skill Discovery — no se va a hacer.
- Nuestro auditor interno (el que sí distingue N/A de FAIL) subió en paralelo a Agent Readiness 97/100, AEO Technical 90/100.

## Subida a GoDaddy vía API de cPanel (3 sep 2026) — método nuevo
Yudit dio un token de API de cPanel para que Claude suba archivos directamente, sin escribir su contraseña. Datos (el token se puede revocar/regenerar en cPanel → Seguridad → Administrar tokens de API):
- Host: `p3plzcpnl507351.prod.phx3.secureserver.net:2083`
- Usuario de cPanel: `w2qunzkx9nhe` (⚠️ NO es el email de GoDaddy — la primera vez Yudit dio el email y falló con 401)
- Auth: header `Authorization: cpanel <usuario>:<token>`
- Subir contenido de un archivo: `POST https://<host>/execute/Fileman/save_file_content` con `dir=public_html`, `file=<nombre>`, `content@<ruta-local>`
- Leer contenido: `POST https://<host>/execute/Fileman/get_file_content` con `dir` y `file`
- Antes de sobrescribir se respaldó el contenido en vivo de las 5 páginas en `C:\Claude\projects\pulidotax-website\backup-antes-deploy-2026-09-03\`.

Con esto, el flujo de "editar y subir manualmente por File Manager" que hacían las tareas automáticas del blog ya puede automatizarse completo si Yudit quiere (guardar este token en algún lugar seguro si se va a reutilizar — no está guardado en memoria de Claude por seguridad, solo el método).

## Más contexto
Memoria completa del proyecto (reglas de la dueña, historial, causa de fallos pasados, formulario de contacto, Google Business Profile): `project_website_pulido_tax.md` en la memoria de Claude.
