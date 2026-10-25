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

**Bloque en la página de inicio — AHORA CON LAS DOS CALCULADORAS (reestructurado el 23 oct 2026):** sección `.toolband` entre Servicios y Cómo trabajamos. Se decidió NO poner dos bandas azules seguidas: la banda pasó de «texto + tarjeta» a «encabezado centrado + dos tarjetas» (`.toolband-head` + `.toolcards`, grid de 2 columnas que colapsa a 1 en móvil). Las tarjetas usan `display:flex;flex-direction:column` con `.tc-foot{margin-top:auto}` para que queden exactamente de la misma altura (verificado: 661px ambas).
- **Tarjeta 1 (impuesto federal):** contratista soltero, $60,000 − $15,000 → SE tax $6,358, renta $2,221, **$2,145 por trimestre**.
- **Tarjeta 2 (Sales Tax):** carro de $20,000 en Osceola → estatal $1,200, recargo **$75** (sin el tope habrían sido $300), total **$21,275**. Se eligió este ejemplo porque el ahorro de $225 en una sola venta es lo que mejor demuestra que vale la pena saber la regla.
- Los números salen del cálculo real verificado. **Si se cambian las cifras fiscales hay que actualizarlos en tres sitios: la calculadora, la tarjeta del inicio y el `index.md`.**
- La página de inicio tiene ahora 3 enlaces a cada calculadora (menú, botón de la tarjeta, pie).

## Hero de la página de inicio: las herramientas ya no están ocultas (24 oct 2026)
Yudit vio que las calculadoras estaban "un poco ocultas": solo estaban en el menú y en una banda más abajo. **Cambios en `index.html`:**
- **Franja `.hero-tools` bajo los botones principales:** etiqueta «Gratis · sin registro», dos tarjetas-botón en lenguaje de acción («Calcule sus impuestos» / «Calcule su Sales Tax», con subtítulo «Independientes, W-2 y Uber» y «Los 67 condados de Florida») y un enlace «…o lea nuestras guías del IRS en español →» al blog. Traducida a EN. 3 enlaces nuevos al blog en la página de inicio (menú, hero, pie).
- **Compactación para que quepa sin bajar:** margen superior del hero 190→142 px, `h1` de 64→58 px (acento 46→42), márgenes menores. Medido: a 1280×720 y 1366×768 los botones y las dos tarjetas quedan dentro de la pantalla; a 901–1180 px las tarjetas se apilan.
- **Móvil (≤900 px):** se quitó `.hero-figure{order:-1}` → **el texto va antes que la foto** (antes la primera pantalla del teléfono era solo la foto). Márgenes del hero reducidos y, a ≤600 px, los dos botones principales van lado a lado (`flex:1`, `nowrap`). Medido a 375×812: título, mensaje, ambos botones, las dos calculadoras y el enlace al blog caben en la primera pantalla.
- **Probado y descartado:** una fila de chips con los 4 servicios en el hero. Ocupaba ~86 px y empujaba las calculadoras fuera de la pantalla; los servicios siguen en «Ver servicios» y en el menú. Las tarjetas de la primera versión salían de 118 px por el texto largo — se acortaron los textos (ahora 60 px).
- **Si se agrega más al hero, volver a medir** que la franja siga entrando en ~700 px de alto.

## Calculadora de impuestos: ahora para W-2 + Uber, con hijos y millas (24 oct 2026)
Motivo: un amigo de Yudit (persona natural, W-2, dependientes, hace Uber) entró y no supo usarla. Probada con su perfil, **la calculadora daba una respuesta equivocada**: no tenía campo para dependientes, y para una familia así el error es de miles de dólares (con 2 hijos, de unos $750 a favor a ~$5,100 a favor).

**Tres cambios en `calculadora.html`:**
1. **Hijos menores de 17** (stepper 0–10). Crédito de hasta $2,200 por hijo; la parte reembolsable es el menor de lo que sobra del crédito, $1,700 por hijo y 15% del ingreso del trabajo sobre $2,500. Se reduce $50 por cada $1,000 (o fracción) sobre $200,000 ($400,000 en conjunto). **Solo baja el impuesto sobre la renta, no el self-employment tax.** El reembolsable entra como crédito en el saldo, no en el "total estimado".
2. **Aviso arriba + botón «Ver un ejemplo: W-2, Uber y 2 hijos»** que rellena el formulario (`loadExample()`). Además 3 preguntas nuevas en las FAQ (HTML + JSON-LD), título/meta orientados a Uber, y el texto de la tarjeta de la página de inicio.
3. **Cuadro de millas** (`<details>`, 2 casillas por periodo): 72.5¢ ene–jun y 76¢ jul–dic de 2026, sumadas a los gastos.

**Cambio de comportamiento NO pedido, pero necesario para este perfil:** el «pago por trimestre» antes era siempre total/4, sin descontar lo retenido en el W-2 — a una persona con reembolso le decía «$937 por trimestre». Ahora es (total − retenido − crédito reembolsable)/4, y **si queda menos de $1,000 por deber muestra «Sin pagos trimestrales»** (regla de $1,000 del IRS). Para independientes puros sin retención no cambia, salvo cuando el total es < $1,000.

**Cifras verificadas en fuente oficial (nunca búsquedas web):**
- Crédito $2,200 y reembolsable $1,700 (2026): **Rev. Proc. 2025-32**, leída del PDF.
- Fórmula del 15% sobre $2,500, umbrales $200k/$400k, redondeo a múltiplos de $1,000 y ×5% (= $50 por $1,000), y la regla especial de 3+ hijos: **PDF del Schedule 8812 (formulario e instrucciones, año 2025)** — `irs.gov/pub/irs-pdf/f1040s8.pdf` y `i1040s8.pdf`. Ojo: son de 2025; los umbrales son de ley y no se indexan, los montos de 2026 sí salen de la Rev. Proc.
- Millas: **página de tarifas del IRS** (72.5¢ ene–jun, IR-2025-128; 76¢ jul–dic, IR-2026-29). **La búsqueda web daba 72.5¢ para todo el año y luego 76¢ sin aclarar el periodo** — solo la página oficial lo desambiguó.
- Peajes y estacionamiento aparte, y millas **o** gastos reales: **Pub. 463, tabla 1-1**. SE tax desde $400 de ganancia neta: **IRS Tema 554**.

**Fuera de alcance a propósito (y dicho en la página):** crédito por ingreso del trabajo (EITC) — con este perfil probablemente aplicaría y haría el reembolso aún mayor —, crédito de $500 por otros dependientes, cuidado de niños. Con 3+ hijos solo se usa la fórmula del 15% y la página lo advierte.

**Probada** con 9 escenarios contra una **referencia independiente en Python escrita desde las reglas** (no copiada del JS): regresión del caso base (alimenta la tarjeta de inicio, $2,145), el amigo ($5,094 a favor), solo W-2 con hijos, 3 hijos en conjunto, ingreso alto con recorte del crédito, ingreso del trabajo < $2,500, ganancia chica sin pagos trimestrales, solo millas, W-2 + Uber sin hijos. **Los 9 coinciden**, primero en local y luego en la página publicada.

**Bug mío de la semana pasada, encontrado y arreglado en las DOS calculadoras:** las filas del desglose tenían `<span class="k" data-i18n="x">Texto <em data-i18n="xe">subtítulo</em></span>`. `setLang()` reemplaza el `textContent` de la etiqueta madre y **borraba el `<em>` para siempre** al cambiar de idioma (se perdían los subtítulos tipo «Seguro Social y Medicare · 15.3%»). Ahora la madre no lleva `data-i18n` y cada pieza tiene el suyo. **Regla: nunca poner `data-i18n` en un elemento que contenga otro elemento traducible.**

## Calculadora de Sales Tax de Florida (23 oct 2026)
`sales-tax.html` + `sales-tax.md` — séptima página. Complementa a `calculadora.html` (que en sus FAQ ya decía que el Sales Tax es una obligación aparte). Sin gate, igual que la otra.

**Dos modos** (pestañas arriba del formulario):
1. *¿Cuánto le cobro al cliente?* — precio + condado (+ casilla «es un solo artículo») → estatal, recargo, total a cobrar.
2. *¿Cuánto le debo al estado?* — ventas gravables del período + condado (+ monto exento + casilla «a tiempo») → impuesto total, descuento, a remitir.

**Reglas y cifras — todas de fuente oficial, nunca de búsquedas web:**
- Tasa estatal 6%; recargos de condado 0%–2% (combinado 6%–8%).
- **Los 67 condados** cargados desde el **Formulario DR-15DSS R. 11/25** (año calendario 2026), extraído del PDF con pypdf. Sin recargo: Citrus y Collier. El más alto: Hamilton 2%.
- El recargo se cobra **según el condado de ENTREGA**, no donde está el negocio (instrucciones DR-15N R. 10/25).
- **Tope de $5,000:** el recargo solo aplica a los primeros $5,000 de *cada venta individual de propiedad personal tangible*; el 6% estatal va sobre el precio completo. Es **por artículo, no por factura**. No aplica a transient rentals. (Ejemplo oficial: artículo de $7,000 → $2,000 en la línea 15(a).)
- **Descuento por presentar a tiempo:** 2.5% de los primeros $1,200 del impuesto, máx. $30, solo si presenta Y paga en línea Y a tiempo.
- Vence el día 1 del mes siguiente, tardío después del día 20. Frecuencia: >$1,000/año mensual; $501–1,000 trimestral; $101–500 semestral; ≤$100 anual.
- **Renta comercial: derogada desde el 1 oct 2025** (TIP 25A01-04) — por eso NO se construyó esa función; ya no existe. Sí siguen gravados equipos, estacionamiento/almacenaje de vehículos y alojamiento ≤6 meses.
- Fuera de alcance a propósito (y dicho en el aviso): casas móviles nuevas 3%, máquinas de entretenimiento 4%, electricidad 6.95%, transient rentals, vending, impuestos turísticos de condado.

**IMPORTANTE — las búsquedas web daban tasas CONTRADICTORIAS entre sí** (rangos 0.5–1.5% vs 0.5–2%, condados con datos vencidos, una fuente aplicaba el tope por transacción en vez de por artículo). Solo el PDF oficial sirvió. Se escribió un verificador (`scratchpad/verify_counties.py`, efímero) que compara **los 67 condados de la página contra el PDF uno por uno**: 0 diferencias.

**Mantenimiento:** las tasas cambian casi siempre el 1 de enero. En 2026 cambiaron Jackson, Martin y Palm Beach. **Varios recargos vencen el 31 dic 2026: Brevard, Charlotte, Liberty (.5%) y Santa Rosa (.5%)** — hay que actualizar el array `COUNTIES` del `<script>`, la nota `rt_note` y los textos del `.md` con la DR-15DSS de 2027.

**Probada** con 11 escenarios (servicio normal, carro de $20,000 con y sin la casilla de artículo, condado sin recargo, Hamilton al 8%, justo en el tope de $5,000, ventas del mes a tiempo y tarde, ventas pequeñas donde el descuento no llega a $30, exenciones, mes sin ventas) — réplica en Python y luego el código real en el navegador, resultados idénticos. También el buscador de condados (encuentra «st john» sin punto) y el toggle ES|EN.

**Arreglo de nav que salió de paso (aplicado a las 7 páginas):** con el séptimo enlace el menú **se partía en dos filas entre ~900px y ~1120px** (laptops). No era culpa del enlace: el menú ya estaba al límite. Se añadió un `@media(max-width:1120px)` con SOLO las reglas de nav, que pasa al menú desplegable antes de que se parta; las reglas de nav se sacaron del bloque de 900px en las 3 páginas de la familia nueva. Medido: a 1086px se partía, a 1125px cabe en una fila.

## Arreglo del selector de idioma en las 6 páginas (22 oct 2026)
Al probar la calculadora salieron **dos fallos reales del sitio**, ya corregidos en las 6 páginas:

1. **Dos claves de almacenamiento distintas.** `index.html` y `calculadora.html` guardaban en `ptax-lang`; `servicios/sobre-mi/blog/contacto` en `ptaLang`. Consecuencia: quien ponía el sitio en inglés en el inicio y pasaba a Servicios **volvía a español**. Afectaba a todo visitante de habla inglesa que navegara el sitio.
2. **`localStorage` sin protección.** En las 4 páginas del grupo `ptaLang`, `localStorage.setItem` era la PRIMERA línea de `setLang`, así que con el almacenamiento bloqueado (incógnito, cookies desactivadas) la función lanzaba excepción y **el botón EN no hacía absolutamente nada**. En `index.html` fallaba a medias (cambiaba `lang` pero no los textos).

**Arreglo:** helpers `rememberLang` / `recallLang` con try/catch en las 6 páginas; se **escriben las dos claves y se lee cualquiera**, así nadie pierde la preferencia que ya tenía guardada y todas las páginas se ponen de acuerdo. Verificado en vivo: las 6 tienen ambos helpers y la doble clave; probado en navegador que el toggle va y vuelve en las 6 sin errores de consola.

⚠️ **Aviso para ediciones masivas:** el intento de aplicar esto con `perl -0pi -e` falló a medias — la sustitución multilínea no coincidió pero la de una línea sí, dejando las 4 páginas llamando a `recallLang()` sin que la función existiera (habría roto el JS en producción). Se detectó al verificar. **Para cambios multilínea usar la herramienta Edit, no perl/sed.** Lo mismo pasó con un comentario `/* */` que quedó con doble cierre y habría roto el script de la calculadora.

También se agregó `calculadora.md` (el `.htaccess` ya lo sirve solo: la regla `^([a-z-]+)\.html$` cubre la página nueva sin tocar nada) y el enlace «Calculadora» en el menú, el menú móvil y el pie de las 5 páginas existentes, más la línea de páginas relacionadas de los 5 `.md`.

**Bug viejo CORREGIDO (22 oct):** `index.html` tenía un enlace suelto a Blog pegado al botón «Conocer mi historia →» en la sección Sobre mí (resto de una inserción automática vieja). Yudit lo vio navegando el sitio en vivo y pidió quitarlo. La página de inicio quedó con 2 enlaces a `blog.html` (menú y pie).

## Artículos con página propia (23 oct 2026) — CAMBIO DE ARQUITECTURA
Antes los 25 artículos vivían en ventanas emergentes dentro de `blog.html`: **sin URL propia**, imposibles de compartir desde Instagram e imposibles de indexar por separado en Google. Ahora cada uno tiene su página.

- **25 páginas nuevas**, una por artículo, con slug en español **elegido a mano y permanente** (ver `SLUGS` en el generador y el mapa en `blog.md`). Cada una con title y meta description propios, canonical, Open Graph, JSON-LD de `Article` + `BreadcrumbList`, migas de pan y enlaces anterior/siguiente.
- **`articulo.css`** — hoja compartida por todas. Las páginas quedan en ~19 KB, el navegador la cachea una vez y un cambio de diseño se hace en un solo sitio. ⚠️ La ruta debe ser **relativa** (`articulo.css`), no `/articulo.css`: el sitio es plano y así además se puede previsualizar en local.
- **`blog.html` es ahora solo el índice**: tarjetas y títulos enlazan a las páginas; fuera los 25 modales, su JS y su CSS. De 172 KB a 65 KB (−62%). Filtros, orden e idioma siguen funcionando.
- **`sitemap.xml`**: 32 URLs (7 páginas + 25 artículos con su fecha real de publicación).
- **`blog.md`**: cada entrada lleva ahora `Leer: https://pulidotax.com/<slug>.html`.
- **`plantilla-articulo.html`** (en la raíz del proyecto, NO se sube al sitio): plantilla con 14 marcadores `{{...}}` que usa la tarea semanal para crear cada artículo nuevo. Probada rellenándola con datos de ensayo.

**Cómo se verificó:** comparación párrafo a párrafo (mismo número de `<p>`, `<h3>` y `<li>` que el original) en las 25; un solo `<h1>`, canonical propio y 2 bloques JSON-LD en cada una; cero enlaces rotos en las 32 páginas; y prueba en navegador contra un servidor local.

**Dos tropiezos que costaron tiempo, anotados para no repetirlos:**
1. `blog.html` usa finales de línea **CRLF**. Los patrones con `\n` no coinciden — hay que usar `\r?\n`. (El `cat -A` me lo ocultó porque sustituí el símbolo de fin de línea.)
2. Al borrar las funciones de los modales con regex quedó un `});` suelto que rompía todo el JavaScript de la página. **Después de tocar JS con script, hay que cargar la página en un navegador y mirar la consola** — el error no se ve de otra forma. Ojo: la consola del panel conserva errores de cargas anteriores; para descartar falsos positivos, abrir pestaña nueva.

**Previsualización local:** `.claude/launch.json` define el servidor `pulidotax-estatico` (python http.server en el puerto 8765 sobre `sitio-pulidotax`). Hace falta porque el panel renderiza los archivos locales como instantánea y las rutas relativas (el CSS externo) no resuelven.

## Automatización del blog
Dos tareas programadas (Claude Code scheduled tasks) mantienen el blog al día — **ya actualizadas para apuntar a esta carpeta** en vez de Downloads:
- `articulo-semanal-blog-pulidotax` — lunes 9 AM, escribe el artículo de la semana.
- `verificar-blog-pulidotax` — martes y jueves 10 AM, vigilante que rellena si falta.

**Ambas tareas reescritas el 23 oct 2026** para la arquitectura nueva. El flujo semanal pasó de 9 a 13 pasos y ahora: elige el slug (permanente, con reglas), **crea la página del artículo rellenando `plantilla-articulo.html`**, **enlaza el artículo anterior con el nuevo** (sustituye su `<div class="ph"></div>` por el enlace "siguiente"), añade la tarjeta al índice, actualiza `blog.md` y `sitemap.xml`, y **sube CINCO archivos** por cPanel (página nueva, página anterior modificada, blog.html, blog.md, sitemap.xml). El vigilante ahora comprueba dos cosas más: que la página del artículo responda 200 y que esté en el sitemap.

**Verificación previa al primer lunes (sábado 24 oct 2026):** como el artículo del lunes 26 aún no existía, no se pudo revisar su resultado; se verificó que todo estuviera listo con una **prueba en seco sobre copias** (`herramientas/prueba-en-seco-semanal.py`, simula los pasos 3–9 con un título difícil con `&`, `$` y acentos). Encontró y se corrigió:
1. **Ancla de inserción en `blog.html` no única:** el cierre del grid (`    </div>` / `  </div>` / `</section>`) aparece **4 veces**; el Edit real habría fallado o insertado mal. Ahora la ancla es el cierre de la **última tarjeta**, que lleva el slug del artículo anterior (única, comprobado).
2. **Párrafo «ORDEN DE EJECUCIÓN»** citaba números de paso viejos y el PASO 0 mandaba al PASO 11 en vez del 13; el PASO 9 estaba redactado de forma confusa; el PASO 10 decía «CUATRO archivos» y listaba cinco. Reescritos. El orden ahora es: 0–9 en local → registro provisional (13) → subida (10) → 11 y 12 → registro final (13).
3. **Regla de títulos:** sin `&` ni comillas dobles (el mismo texto va en `<title>`, JSON-LD y `<h1>`).
4. **Hueco del vigilante:** si el lunes el artículo se creaba en local pero la subida fallaba, el vigilante del martes veía que faltaba en vivo y escribía OTRO artículo. Nuevo **PASO 2b**: si el `blog.html` local ya tiene la tarjeta de esta semana, solo sube lo pendiente (5 archivos) y registra «RESCATADO».
También se confirmó: la conexión a GoDaddy responde; ambas tareas activas (lunes 09:13, martes/jueves 10:00); los permisos de `~/.claude/settings.json` cubren todos los comandos nuevos (`Edit/Write` del proyecto, `curl -s *`, `date`, `ls`, `cp`, `git`); y **la forma exacta del comando de subida (`--data-urlencode "content@…"`) funciona y conserva los acentos** — se probó subiendo `blog.md` idéntico y comparando con lo publicado. El skill `pulido-tax-editor` no tiene instrucciones sobre modales (no contradice nada).
**Limitación que sigue:** si la app está cerrada el lunes a las 9:13, la tarea se difiere hasta que Yudit la abra. **Cuando pase el lunes, revisar:** `logs/ultima-ejecucion.txt`, que `pulidotax.com/blog.html` tenga una tarjeta del 26 oct, que la página del artículo dé 200, que esté en `sitemap.xml`, y que la página del artículo del 19 oct enlace al nuevo («Artículo siguiente»).

Verificado que todas las rutas que mencionan las tareas existen y que los puntos de inserción (el `ph` del último artículo, el comentario del sitemap, el final del grid) están tal como las tareas los esperan.

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

## 25 oct 2026 — correcciones de calculadora, correo y og:image (publicado)
- calculadora.html: base del QBI = ganancia neta − mitad del SE tax (deducción = menor entre 20% de la base y 20% del gravable antes de QBI; mínimo $400 evaluado sobre esa base); SE tax = $0 si neta × 0.9235 < $400 (también aplica al Medicare adicional). Verificado contra referencia independiente en 17 escenarios. Ejemplo del amigo (W-2 + Uber, 2 hijos): reembolso $5,082 (antes $5,094). Tarjeta del inicio sin cambio ($8,579 / $2,145 trimestral).
- blog.html: mailto ypulido87@gmail.com → yudit@pulidotax.com. Pendiente ofrecido: teléfono/correo siguen en el HTML estático del blog (ocultos tras el botón), las otras páginas los arman con JavaScript.
- og:title/description/image(+width/height/alt) en las 32 páginas y en plantilla-articulo.html; twitter:card summary_large_image. Imagen: sitio-pulidotax/og-image.png (1200×630, logo real: rombo doble contorno + P), subida por upload_files.
