# -*- coding: utf-8 -*-
"""Publica el articulo semanal del blog de pulidotax.com de principio a fin.

Claude (la tarea programada) solo INVESTIGA y ESCRIBE el articulo en un archivo JSON.
Este programa hace TODO lo mecanico, siempre igual, sin pedir permisos:
  1. valida el JSON            2. crea la pagina desde la plantilla
  3. enlaza el articulo anterior   4. tarjeta en blog.html   5. entrada en blog.md
  6. entrada en sitemap.xml    7. verificaciones   8. sube 5 archivos a GoDaddy (cPanel)
  9. verifica en vivo         10. registro del skill (2 copias)   11. bitacora

Uso:
  python publicar_articulo.py                 publica articulo-de-la-semana.json
  python publicar_articulo.py --prueba        ensayo sobre copias temporales: no sube nada
  python publicar_articulo.py --fecha AAAA-MM-DD   usa esa fecha en vez de hoy
  python publicar_articulo.py --forzar        publica aunque ya haya articulo de esta semana

Si algo falla DESPUES de crear los archivos locales, se puede volver a correr el mismo
comando: detecta lo ya hecho y solo reintenta la subida y lo que falte.
Ultima linea que imprime:  PUBLICADO <url>  |  YA HABIA ARTICULO ...  |  ERROR <paso>: <motivo>
"""
import datetime
import json
import math
import os
import re
import shutil
import sys
import tempfile
import time
import urllib.parse
import urllib.request
import xml.dom.minidom

RAIZ = r'C:\Claude\projects\pulidotax-website'
SITIO_REAL = os.path.join(RAIZ, 'sitio-pulidotax')
PLANTILLA = os.path.join(RAIZ, 'plantilla-articulo.html')
JSON_ARTICULO = os.path.join(RAIZ, 'articulo-de-la-semana.json')
LOGS = os.path.join(RAIZ, 'logs')
BITACORA = os.path.join(LOGS, 'ultima-ejecucion.txt')
REGISTRO = r'C:\Claude\projects\pulido-tax-editor\references\published-articles.md'
REGISTRO_SKILL = r'C:\Users\yudit\.claude\skills\pulido-tax-editor\references\published-articles.md'
CABECERA = r'C:\Users\yudit\.claude\cpanel-header.txt'
CPANEL = 'https://p3plzcpnl507351.prod.phx3.secureserver.net:2083/execute/Fileman/save_file_content'
DOMINIO = 'https://pulidotax.com'

CATEGORIAS = {
    'personal': 'Impuestos personales',
    'llc': 'Negocios y LLC',
    'nomina': 'Nómina',
    'fechas': 'Fechas límite',
    'irs': 'Cambios del IRS',
}
MESES = ['enero', 'febrero', 'marzo', 'abril', 'mayo', 'junio', 'julio', 'agosto',
         'septiembre', 'octubre', 'noviembre', 'diciembre']
PROHIBIDO_EN_TEXTO = [
    (r'\(?689\)?[\s\-.]*270[\s\-.]*8845', 'telefono visible'),
    (r'yudit@pulidotax\.com', 'email visible'),
    (r'biling', 'palabra "bilingue"'),
    (r'\{\{', 'marcador {{ sin sustituir'),
    (r'<h1', 'etiqueta <h1> dentro del cuerpo'),
    (r'<script', 'etiqueta <script> dentro del cuerpo'),
]

try:
    sys.stdout.reconfigure(encoding='utf-8')
except Exception:
    pass

PRUEBA = '--prueba' in sys.argv
FORZAR = '--forzar' in sys.argv
FECHA_ARG = None
if '--fecha' in sys.argv:
    FECHA_ARG = sys.argv[sys.argv.index('--fecha') + 1]


class Fallo(Exception):
    def __init__(self, paso, motivo):
        super().__init__('%s: %s' % (paso, motivo))
        self.paso = paso
        self.motivo = motivo


def leer(ruta):
    with open(ruta, 'r', encoding='utf-8', newline='') as f:
        return f.read()


def escribir(ruta, texto):
    with open(ruta, 'w', encoding='utf-8', newline='') as f:
        f.write(texto)


def hoy():
    if FECHA_ARG:
        return datetime.date.fromisoformat(FECHA_ARG)
    return datetime.date.today()


def fecha_texto(d):
    return '%d de %s, %d' % (d.day, MESES[d.month - 1], d.year)


# ---------------------------------------------------------------- bitacora
LINEAS_LOG = []


def log(msg):
    LINEAS_LOG.append(msg)
    print(msg)


def guardar_bitacora(resultado, extra=''):
    if PRUEBA:
        return
    ahora = datetime.datetime.now().strftime('%Y-%m-%d %H:%M')
    cuerpo = 'Fecha y hora: %s — publicar_articulo.py (tarea articulo-semanal-blog-pulidotax)\n' % ahora
    cuerpo += 'Resultado: %s\n' % resultado
    if extra:
        cuerpo += extra.rstrip() + '\n'
    cuerpo += '\nDetalle:\n' + '\n'.join('  ' + l for l in LINEAS_LOG) + '\n'
    os.makedirs(LOGS, exist_ok=True)
    escribir(BITACORA, cuerpo)


# ---------------------------------------------------------------- validacion
def cargar_articulo():
    if not os.path.exists(JSON_ARTICULO):
        raise Fallo('entrada', 'no existe %s (Claude no dejo el articulo)' % JSON_ARTICULO)
    try:
        a = json.loads(leer(JSON_ARTICULO))
    except ValueError as e:
        raise Fallo('entrada', 'el JSON no es valido: %s' % e)
    for k in ('titulo', 'slug', 'categoria', 'descripcion', 'extracto', 'cuerpo_html'):
        if not str(a.get(k, '')).strip():
            raise Fallo('entrada', 'falta el campo "%s"' % k)
    for k in ('titulo', 'descripcion', 'extracto'):
        if '&' in a[k] or '"' in a[k] or '\\' in a[k] or '<' in a[k]:
            raise Fallo('entrada', 'el campo "%s" no puede llevar & " \\ ni < (usar «y» y « »)' % k)
    if not re.fullmatch(r'[a-z0-9]+(-[a-z0-9]+){2,6}', a['slug']):
        raise Fallo('entrada', 'slug invalido: solo minusculas, numeros y guiones, 3 a 7 palabras')
    if a['categoria'] not in CATEGORIAS:
        raise Fallo('entrada', 'categoria invalida: %s' % ', '.join(CATEGORIAS))
    if not 100 <= len(a['descripcion']) <= 170:
        log('AVISO: la descripcion mide %d caracteres (ideal 150-158)' % len(a['descripcion']))
    for campo in ('titulo', 'descripcion', 'extracto', 'cuerpo_html'):
        for patron, que in PROHIBIDO_EN_TEXTO:
            if re.search(patron, a[campo], re.I):
                raise Fallo('entrada', 'el campo "%s" contiene %s' % (campo, que))
    if len(re.findall(r'\w+', re.sub(r'<[^>]+>', ' ', a['cuerpo_html']))) < 350:
        raise Fallo('entrada', 'el cuerpo es demasiado corto (menos de 350 palabras)')
    if '<p' not in a['cuerpo_html']:
        raise Fallo('entrada', 'el cuerpo debe estar en HTML (<p>, <h3>, <ul><li>)')
    reg = a.get('registro') or {}
    for k in ('category', 'primary_topic', 'primary_keyword', 'main_source', 'reason'):
        if not str(reg.get(k, '')).strip():
            raise Fallo('entrada', 'falta registro.%s (para el registro del skill)' % k)
    return a


# ---------------------------------------------------------------- piezas
def lunes_de(d):
    return d - datetime.timedelta(days=d.weekday())


def fechas_blog(blog_html):
    return sorted(set(re.findall(r'data-date="(\d{4}-\d{2}-\d{2})"', blog_html)))


def anterior_de(sitio, blog_md, slug_nuevo):
    """Slug y titulo del articulo mas reciente que NO sea el nuevo (primero de blog.md)."""
    for m in re.finditer(r'Leer: https://pulidotax\.com/([a-z0-9\-]+)\.html', blog_md):
        s = m.group(1)
        if s != slug_nuevo:
            pagina = leer(os.path.join(sitio, s + '.html'))
            h1 = re.search(r'<h1>(.*?)</h1>', pagina, re.S)
            if not h1:
                raise Fallo('anterior', 'no encuentro el <h1> de %s.html' % s)
            return s, h1.group(1).strip()
    raise Fallo('anterior', 'no encuentro el articulo anterior en blog.md')


def construir_pagina(a, d, ant_slug, ant_titulo):
    tpl = leer(PLANTILLA)
    lectura = a.get('lectura') or '%d min' % max(2, math.ceil(
        len(re.findall(r'\w+', re.sub(r'<[^>]+>', ' ', a['cuerpo_html']))) / 200.0))
    cuerpo = '\n'.join(('        ' + l.strip()) if l.strip() else '' for l in a['cuerpo_html'].strip().splitlines())
    wa_texto = a.get('whatsapp_texto') or 'Hola, leí el artículo «%s» y tengo una pregunta.' % a['titulo']
    valores = {
        'TITULO': a['titulo'], 'TITULO_HTML': a['titulo'], 'DESCRIPCION': a['descripcion'],
        'SLUG': a['slug'], 'FECHA_ISO': d.isoformat(), 'FECHA_TEXTO': fecha_texto(d),
        'LECTURA': lectura, 'CATEGORIA': a['categoria'], 'CATEGORIA_TEXTO': CATEGORIAS[a['categoria']],
        'EXTRACTO': a['extracto'], 'CUERPO': cuerpo,
        'WHATSAPP': 'https://wa.me/16892708845?text=' + urllib.parse.quote(wa_texto),
        'ANTERIOR_SLUG': ant_slug, 'ANTERIOR_TITULO': ant_titulo,
    }
    for k, v in valores.items():
        tpl = tpl.replace('{{%s}}' % k, v)
    if '{{' in tpl:
        raise Fallo('pagina', 'quedaron marcadores sin sustituir: %s' % re.findall(r'\{\{\w+\}\}', tpl))
    return tpl, lectura


def enlazar_anterior(sitio, ant_slug, a):
    ruta = os.path.join(sitio, ant_slug + '.html')
    html = leer(ruta)
    if 'href="%s.html" class="next"' % a['slug'] in html:
        log('anterior: ya estaba enlazado')
        return
    m = re.search(r'(<nav class="art-nav".*?</nav>)', html, re.S)
    if not m or m.group(1).count('<div class="ph"></div>') != 1:
        raise Fallo('enlace', 'no encuentro UN <div class="ph"></div> en el art-nav de %s.html' % ant_slug)
    nuevo_nav = m.group(1).replace(
        '<div class="ph"></div>',
        '<a href="%s.html" class="next"><div class="lbl" data-i18n="a_next">Artículo siguiente</div>'
        '<div class="t">%s</div></a>' % (a['slug'], a['titulo']))
    escribir(ruta, html.replace(m.group(1), nuevo_nav, 1))
    log('anterior: %s.html enlazado al nuevo' % ant_slug)


def tarjeta_blog(sitio, a, d, ant_slug, lectura):
    ruta = os.path.join(sitio, 'blog.html')
    html = leer(ruta)
    if 'href="%s.html"' % a['slug'] in html:
        log('blog.html: la tarjeta ya estaba')
        return
    antes = html.count('<article class="post-card')
    nl = '\r\n' if '\r\n' in html else '\n'
    ancla = re.compile(
        r'(          <a class="post-more" href="%s\.html">.*?</a>\r?\n        </div>\r?\n      </article>)' % re.escape(ant_slug),
        re.S)
    ms = list(ancla.finditer(html))
    if len(ms) != 1:
        raise Fallo('tarjeta', 'el ancla de la ultima tarjeta aparece %d veces (debe ser 1)' % len(ms))
    c = a['categoria']
    tarjeta = (
        '      <article class="post-card reveal" data-cat="%(c)s" data-date="%(f)s">\n'
        '        <div class="post-band band-%(c)s" data-i18n="f-%(c)s">%(ct)s</div>\n'
        '        <div class="post-body">\n'
        '          <p class="post-date">%(ft)s</p>\n'
        '          <h2 class="post-title"><a href="%(s)s.html">%(t)s</a></h2>\n'
        '          <p class="post-excerpt">%(e)s</p>\n'
        '          <p class="post-meta"><span data-i18n="read-time">Tiempo de lectura</span>: %(l)s</p>\n'
        '          <a class="post-more" href="%(s)s.html"><span data-i18n="read-more">Leer más →</span></a>\n'
        '        </div>\n'
        '      </article>' % {'c': c, 'f': d.isoformat(), 'ct': CATEGORIAS[c], 'ft': fecha_texto(d),
                              's': a['slug'], 't': a['titulo'], 'e': a['extracto'], 'l': lectura})
    m = ms[0]
    nuevo = html[:m.end()] + nl + nl + tarjeta.replace('\n', nl) + html[m.end():]
    escribir(ruta, nuevo)
    despues = nuevo.count('<article class="post-card')
    if despues != antes + 1:
        raise Fallo('tarjeta', 'tarjetas %d -> %d (debia ser +1)' % (antes, despues))
    log('blog.html: tarjeta añadida (%d -> %d)' % (antes, despues))


def entrada_blog_md(sitio, a, d):
    ruta = os.path.join(sitio, 'blog.md')
    md = leer(ruta)
    if 'Leer: %s/%s.html' % (DOMINIO, a['slug']) in md:
        log('blog.md: la entrada ya estaba')
        return
    t = a['titulo']
    punto = '' if t[-1] in '.?!' else '.'
    entrada = '- **[%s] %s — %s%s** %s\n   Leer: %s/%s.html\n\n' % (
        CATEGORIAS[a['categoria']], fecha_texto(d), t, punto, a['extracto'], DOMINIO, a['slug'])
    cab = '## Artículos (más recientes primero)\n\n'
    if md.count(cab) != 1:
        raise Fallo('blog.md', 'no encuentro el encabezado de la lista (o aparece mas de una vez)')
    escribir(ruta, md.replace(cab, cab + entrada, 1))
    log('blog.md: entrada añadida')


def entrada_sitemap(sitio, a, d):
    ruta = os.path.join(sitio, 'sitemap.xml')
    sm = leer(ruta)
    if '<loc>%s/%s.html</loc>' % (DOMINIO, a['slug']) in sm:
        log('sitemap.xml: la entrada ya estaba')
        return
    ancla = '  <!-- Articulos del blog, del mas reciente al mas antiguo -->\n'
    if sm.count(ancla) != 1:
        raise Fallo('sitemap', 'no encuentro el comentario ancla')
    bloque = '  <url>\n    <loc>%s/%s.html</loc>\n    <lastmod>%s</lastmod>\n  </url>\n' % (DOMINIO, a['slug'], d.isoformat())
    escribir(ruta, sm.replace(ancla, ancla + bloque, 1))
    log('sitemap.xml: entrada añadida')


def verificar(sitio, a, d):
    pagina = leer(os.path.join(sitio, a['slug'] + '.html'))
    blog = leer(os.path.join(sitio, 'blog.html'))
    errores = []
    if '{{' in pagina:
        errores.append('pagina con {{')
    if pagina.count('<h1>') != 1:
        errores.append('la pagina debe tener un <h1> (tiene %d)' % pagina.count('<h1>'))
    if 'rel="canonical" href="%s/%s.html"' % (DOMINIO, a['slug']) not in pagina:
        errores.append('canonical incorrecto')
    if blog.count('href="%s.html"' % a['slug']) != 2:
        errores.append('blog.html: el slug debe aparecer 2 veces (%d)' % blog.count('href="%s.html"' % a['slug']))
    if 'modal-overlay' in blog:
        errores.append('blog.html tiene modal-overlay')
    if not blog.rstrip().endswith('</html>'):
        errores.append('blog.html no termina en </html>')
    if not pagina.rstrip().endswith('</html>'):
        errores.append('la pagina no termina en </html>')
    try:
        xml.dom.minidom.parseString(leer(os.path.join(sitio, 'sitemap.xml')).encode('utf-8'))
    except Exception as e:
        errores.append('sitemap.xml no es XML valido: %s' % e)
    if errores:
        raise Fallo('verificacion', '; '.join(errores))
    log('verificacion local: todo correcto')


# ---------------------------------------------------------------- subida
def cabecera_auth():
    with open(CABECERA, 'r', encoding='ascii') as f:
        linea = f.read().strip()
    nombre, _, valor = linea.partition(':')
    return nombre.strip(), valor.strip()


def subir(sitio, nombre):
    k, v = cabecera_auth()
    contenido = leer(os.path.join(sitio, nombre))
    datos = urllib.parse.urlencode({'dir': 'public_html', 'file': nombre, 'content': contenido}).encode('utf-8')
    ultimo = ''
    for intento in range(1, 4):
        try:
            req = urllib.request.Request(CPANEL, data=datos, headers={k: v})
            with urllib.request.urlopen(req, timeout=60) as r:
                resp = json.loads(r.read().decode('utf-8'))
            if resp.get('status') == 1:
                return
            ultimo = 'respuesta sin status 1'
        except Exception as e:
            ultimo = type(e).__name__
        time.sleep(3 * intento)
    raise Fallo('subida', '%s no se pudo subir (%s)' % (nombre, ultimo))


def http(url):
    req = urllib.request.Request(url, headers={'User-Agent': 'publicar_articulo/1.0'})
    with urllib.request.urlopen(req, timeout=40) as r:
        return r.status, r.read().decode('utf-8', 'replace')


def subir_y_verificar(sitio, a, ant_slug):
    archivos = [a['slug'] + '.html', ant_slug + '.html', 'blog.html', 'blog.md', 'sitemap.xml']
    pendientes = []
    for nombre in archivos:
        try:
            subir(sitio, nombre)
            log('subido: %s' % nombre)
        except Fallo as e:
            pendientes.append(nombre)
            log('FALLO al subir %s: %s' % (nombre, e.motivo))
    if pendientes:
        raise Fallo('subida', 'PENDIENTE DE SUBIR: ' + ', '.join(pendientes))
    t = str(int(time.time()))
    estado, cuerpo = http('%s/%s.html?v=%s' % (DOMINIO, a['slug'], t))
    if estado != 200 or a['titulo'] not in cuerpo:
        raise Fallo('verificacion en vivo', 'la pagina nueva no responde 200 con su titulo (%s)' % estado)
    _, sm = http('%s/sitemap.xml?v=%s' % (DOMINIO, t))
    _, bl = http('%s/blog.html?v=%s' % (DOMINIO, t))
    if a['slug'] not in sm or a['slug'] not in bl:
        raise Fallo('verificacion en vivo', 'el sitemap o el blog en vivo aun no muestran el articulo')
    log('en vivo: %s/%s.html -> 200, en sitemap y en blog' % (DOMINIO, a['slug']))


# ---------------------------------------------------------------- registro del skill
def registrar_skill(a, d):
    reg = leer(REGISTRO)
    url = '%s/%s.html' % (DOMINIO, a['slug'])
    if 'URL:** ' + url in reg:
        log('registro: la entrada ya estaba')
    else:
        r = a['registro']
        entrada = ('### %s\n**Title ES:** %s\n**Title EN:**\n**Category:** %s\n**Primary topic:** %s\n'
                   '**Primary keyword:** %s\n**Main official source:** %s\n**Reason selected:** %s\n'
                   '**URL:** %s\n**Status:** Published\n\n') % (
            d.isoformat(), a['titulo'], r['category'], r['primary_topic'], r['primary_keyword'],
            r['main_source'], r['reason'], url)
        cab = '## Existing articles\n\n'
        if reg.count(cab) != 1:
            raise Fallo('registro', 'no encuentro "## Existing articles"')
        escribir(REGISTRO, reg.replace(cab, cab + entrada, 1))
        log('registro del skill: entrada añadida')
    try:
        shutil.copyfile(REGISTRO, REGISTRO_SKILL)
        log('registro: copia del skill instalado sincronizada')
    except Exception as e:
        log('AVISO: no se pudo sincronizar la copia instalada (%s)' % type(e).__name__)


# ---------------------------------------------------------------- principal
def main():
    a = cargar_articulo()
    d = hoy()
    sitio = SITIO_REAL
    if PRUEBA:
        sitio = os.path.join(tempfile.gettempdir(), 'pulidotax-ensayo-publicar')
        if os.path.isdir(sitio):
            shutil.rmtree(sitio)
        shutil.copytree(SITIO_REAL, sitio)
        log('MODO PRUEBA: se trabaja sobre una copia en %s; no se sube nada' % sitio)

    blog = leer(os.path.join(sitio, 'blog.html'))
    pagina_nueva = os.path.join(sitio, a['slug'] + '.html')
    ya_creado = os.path.exists(pagina_nueva) and ('href="%s.html"' % a['slug']) in blog

    if not ya_creado:
        if os.path.exists(pagina_nueva):
            raise Fallo('slug', '%s.html ya existe pero no es de este articulo: cambie el slug' % a['slug'])
        recientes = [f for f in fechas_blog(blog) if f >= lunes_de(d).isoformat()]
        if recientes and not FORZAR:
            print('YA HABIA ARTICULO esta semana (%s). No se publica otro.' % recientes[-1])
            guardar_bitacora('YA HABÍA ARTÍCULO esta semana (%s)' % recientes[-1])
            return 0
        copia = os.path.join(LOGS, 'respaldo-publicacion', d.isoformat())
        if not PRUEBA:
            os.makedirs(copia, exist_ok=True)
            for f in ('blog.html', 'blog.md', 'sitemap.xml'):
                shutil.copyfile(os.path.join(sitio, f), os.path.join(copia, f))
        guardar_bitacora('EN CURSO: %s' % a['titulo'])
        ant_slug, ant_titulo = anterior_de(sitio, leer(os.path.join(sitio, 'blog.md')), a['slug'])
        log('anterior: %s' % ant_slug)
        html, lectura = construir_pagina(a, d, ant_slug, ant_titulo)
        escribir(pagina_nueva, html)
        log('pagina creada: %s.html (%s de lectura)' % (a['slug'], lectura))
        if not PRUEBA:
            shutil.copyfile(os.path.join(sitio, ant_slug + '.html'), os.path.join(copia, ant_slug + '.html'))
        enlazar_anterior(sitio, ant_slug, a)
        tarjeta_blog(sitio, a, d, ant_slug, lectura)
        entrada_blog_md(sitio, a, d)
        entrada_sitemap(sitio, a, d)
    else:
        log('reanudando: los archivos locales ya estaban creados')
        ant_slug, _ = anterior_de(sitio, leer(os.path.join(sitio, 'blog.md')), a['slug'])
    verificar(sitio, a, d)

    if PRUEBA:
        print('PRUEBA OK: todo lo local funciona. Carpeta de ensayo: %s' % sitio)
        return 0

    subir_y_verificar(sitio, a, ant_slug)
    registrar_skill(a, d)
    url = '%s/%s.html' % (DOMINIO, a['slug'])
    destino = os.path.join(LOGS, 'publicados')
    os.makedirs(destino, exist_ok=True)
    shutil.move(JSON_ARTICULO, os.path.join(destino, '%s_%s.json' % (d.isoformat(), a['slug'])))
    guardar_bitacora('PUBLICADO', 'Artículo: "%s"\nURL: %s (HTTP 200 en vivo; en sitemap; tarjeta en blog.html)' % (a['titulo'], url))
    print('PUBLICADO ' + url)
    return 0


def estado():
    """--estado: dice si esta semana ya hay articulo (en local y en vivo). No escribe nada."""
    d = hoy()
    lunes = lunes_de(d).isoformat()
    local = [f for f in fechas_blog(leer(os.path.join(SITIO_REAL, 'blog.html'))) if f >= lunes]
    try:
        _, vivo_html = http('%s/blog.html?v=%d' % (DOMINIO, int(time.time())))
        vivo = [f for f in fechas_blog(vivo_html) if f >= lunes]
    except Exception:
        vivo = None
    print('Hoy: %s | lunes de esta semana: %s' % (d.isoformat(), lunes))
    print('En local: %s | En vivo: %s' % (local[-1] if local else 'NO HAY', (vivo[-1] if vivo else 'NO HAY') if vivo is not None else 'no se pudo consultar'))
    if local and vivo:
        print('ESTADO: HAY ARTICULO ESTA SEMANA (no hacer nada)')
    elif local and vivo is not None:
        print('ESTADO: SUBIDA PENDIENTE (el articulo esta en local pero no en vivo)')
    elif local:
        print('ESTADO: HAY ARTICULO EN LOCAL (no se pudo comprobar en vivo)')
    else:
        print('ESTADO: FALTA EL ARTICULO DE ESTA SEMANA')
    return 0


if __name__ == '__main__':
    if '--estado' in sys.argv:
        sys.exit(estado())
    try:
        sys.exit(main())
    except Fallo as e:
        guardar_bitacora('ERROR en el paso "%s"' % e.paso, 'Motivo: %s\nLos archivos locales quedan hechos; volver a correr el mismo comando reintenta lo que falte.' % e.motivo)
        print('ERROR %s: %s' % (e.paso, e.motivo))
        sys.exit(2)
    except Exception as e:
        guardar_bitacora('ERROR inesperado', '%s: %s' % (type(e).__name__, e))
        print('ERROR inesperado: %s: %s' % (type(e).__name__, e))
        sys.exit(3)
