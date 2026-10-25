# -*- coding: utf-8 -*-
"""PRUEBA EN SECO de la tarea semanal del blog (articulo-semanal-blog-pulidotax).

Simula, sobre COPIAS en la carpeta temporal, los pasos 3 a 9 de la tarea: pagina nueva
desde la plantilla, enlace con el articulo anterior, tarjeta en blog.html, blog.md y
sitemap.xml, mas las verificaciones. NO toca el sitio ni el servidor.

Uso:   python herramientas/prueba-en-seco-semanal.py
Cuando correrla: despues de cambiar blog.html, la plantilla, el sitemap o las
instrucciones de la tarea, y antes de un lunes si se toco algo de eso.
Si algo "FALLA", la tarea real probablemente fallaria igual.

Nota (24 oct 2026): esta prueba encontro que el cierre del grid de blog.html
(4 espacios </div>, 2 espacios </div>, </section>) aparece 4 veces, asi que NO sirve de
ancla; el ancla correcta es el cierre de la ULTIMA tarjeta, que lleva el slug del articulo
anterior. Si cambia el slug del ultimo articulo, actualice `anterior_slug` en el codigo.
"""
import io, os, re, json, shutil, sys
from html.parser import HTMLParser
import xml.dom.minidom

SITE = r'C:\Claude\projects\pulidotax-website\sitio-pulidotax'
TPL = r'C:\Claude\projects\pulidotax-website\plantilla-articulo.html'
import tempfile
TMP = os.path.join(tempfile.gettempdir(), 'pulidotax-prueba-en-seco')

if os.path.isdir(TMP):
    shutil.rmtree(TMP)
os.makedirs(TMP)
for f in os.listdir(SITE):
    p = os.path.join(SITE, f)
    if os.path.isfile(p) and f.endswith(('.html', '.md', '.xml', '.css')):
        shutil.copy(p, TMP)

fails = []


def check(nombre, cond, extra=''):
    print('  %-62s %s %s' % (nombre, 'OK' if cond else 'FALLA', extra))
    if not cond:
        fails.append(nombre)


def rd(name, base=TMP):
    return io.open(os.path.join(base, name), encoding='utf-8', newline='').read()


def wr(name, s):
    io.open(os.path.join(TMP, name), 'w', encoding='utf-8', newline='').write(s)


# ---------------------------------------------------------------- datos de ensayo (peor caso)
SLUG = 'prueba-en-seco-1099-k-uber'
FECHA_ISO, FECHA_TXT = '2026-10-26', '26 de octubre, 2026'
TITULO = 'Uber, DoorDash & Lyft: el umbral del 1099-K es de $5,000 — qué hacer si usted maneja'
DESC = 'Si cobra por manejar, el IRS recibe un informe de lo que usted ganó. Qué cambia en 2026 y cómo prepararse.'
CAT, CAT_TXT = 'irs', 'Cambios del IRS'
EXTRACTO = 'Lo que gana manejando le llega al IRS. Le explicamos qué es el formulario y qué hacer.'
CUERPO = '        <p>Párrafo de prueba con <strong>negrita</strong> y cifras como $5,000.</p>\n        <h3>Subtítulo</h3>\n        <ul>\n          <li>Punto uno</li>\n        </ul>'
WA = 'https://wa.me/16892708845?text=Hola,%20tengo%20dudas%20sobre%20el%201099-K'

print('\n[0] ESTADO INICIAL')
blog = rd('blog.html')
n0 = len(re.findall(r'<article class="post-card', blog))
md0 = rd('blog.md')
e0 = len(re.findall(r'(?m)^\d+\. \*\*\[', md0))
print('  tarjetas en blog.html: %d | entradas en blog.md: %d' % (n0, e0))
check('hay tantas tarjetas como entradas en blog.md', n0 == e0)

# ---------------------------------------------------------------- slug libre
print('\n[1] SLUG')
check('el slug no existe ya', not os.path.exists(os.path.join(SITE, SLUG + '.html')))
check('el slug cumple las reglas (minusculas, numeros, guiones)', re.fullmatch(r'[a-z0-9-]{3,60}', SLUG) is not None)

# ---------------------------------------------------------------- pagina del articulo desde la plantilla
print('\n[2] PAGINA NUEVA DESDE LA PLANTILLA')
tpl = io.open(TPL, encoding='utf-8', newline='').read()
anterior_slug = 'ultimo-pago-estimado-15-de-enero-2027'
anterior_titulo = '15 de enero de 2027: el último pago estimado del año (y cómo saber si usted puede omitirlo)'
datos = {
    'TITULO': TITULO.replace('&', '&amp;'),          # texto plano para <title>, og y JSON-LD
    'TITULO_HTML': TITULO.replace('&', '&amp;'),
    'DESCRIPCION': DESC, 'SLUG': SLUG, 'FECHA_ISO': FECHA_ISO, 'FECHA_TEXTO': FECHA_TXT,
    'LECTURA': '4 min', 'CATEGORIA': CAT, 'CATEGORIA_TEXTO': CAT_TXT, 'EXTRACTO': EXTRACTO,
    'CUERPO': CUERPO, 'WHATSAPP': WA, 'ANTERIOR_SLUG': anterior_slug, 'ANTERIOR_TITULO': anterior_titulo,
}
page = tpl
for k, v in datos.items():
    page = page.replace('{{%s}}' % k, v)
check('no queda ningun marcador {{...}} sin rellenar', '{{' not in page)
wr(SLUG + '.html', page)

lds = re.findall(r'<script type="application/ld\+json">\n?(.*?)\n?</script>', page, re.S)
okjson = True
for b in lds:
    try:
        json.loads(b)
    except Exception as e:
        okjson = False
        print('     JSON-LD invalido:', e)
check('los 2 bloques JSON-LD son JSON valido (titulo con & y $)', okjson and len(lds) == 2)
check('un solo <h1>', page.count('<h1>') == 1)
check('canonical apunta a su propia URL', 'canonical" href="https://pulidotax.com/%s.html"' % SLUG in page)

class Bal(HTMLParser):
    VOID = {'meta', 'link', 'br', 'img', 'input', 'hr', 'path', 'line', 'circle', 'rect', 'polygon', 'polyline', 'source'}
    def __init__(self):
        super().__init__(); self.stack = []; self.bad = []
    def handle_starttag(self, t, a):
        if t not in self.VOID: self.stack.append(t)
    def handle_startendtag(self, t, a): pass
    def handle_endtag(self, t):
        if t in self.VOID: return
        if self.stack and self.stack[-1] == t: self.stack.pop()
        else: self.bad.append(t)

def balanced(html):
    p = Bal(); p.feed(html)
    return not p.bad and not p.stack, (p.bad[:3], p.stack[:3])

ok, info = balanced(page)
check('HTML de la pagina nueva bien formado', ok, '' if ok else str(info))

# ---------------------------------------------------------------- enlazar el articulo anterior
print('\n[3] ENLAZAR EL ANTERIOR CON EL NUEVO')
prev = rd(anterior_slug + '.html')
check('el articulo anterior tiene exactamente 1 hueco <div class="ph"></div>', prev.count('<div class="ph"></div>') == 1,
      '(hay %d)' % prev.count('<div class="ph"></div>'))
nuevo_link = ('<a href="%s.html" class="next"><div class="lbl" data-i18n="a_next">Artículo siguiente</div>'
              '<div class="t">%s</div></a>') % (SLUG, TITULO.replace('&', '&amp;'))
prev2 = prev.replace('<div class="ph"></div>', nuevo_link)
wr(anterior_slug + '.html', prev2)
ok, info = balanced(prev2)
check('el articulo anterior sigue bien formado', ok, '' if ok else str(info))
check('el anterior ahora enlaza al nuevo', ('href="%s.html"' % SLUG) in prev2)

# ---------------------------------------------------------------- tarjeta en el indice
print('\n[4] TARJETA EN blog.html')
NLB = '\r\n' if '\r\n' in blog else '\n'
ancla = N = None
cierre = NLB.join([
    '          <a class="post-more" href="%s.html"><span data-i18n="read-more">Leer más →</span></a>' % anterior_slug,
    '        </div>',
    '      </article>'])
cnt = blog.count(cierre)
check('el ancla (cierre de la ULTIMA tarjeta) es unica', cnt == 1, '(aparece %d)' % cnt)
tarjeta = NLB.join([
    '      <article class="post-card reveal" data-cat="%s" data-date="%s">' % (CAT, FECHA_ISO),
    '        <div class="post-band band-%s" data-i18n="f-%s">%s</div>' % (CAT, CAT, CAT_TXT),
    '        <div class="post-body">',
    '          <p class="post-date">%s</p>' % FECHA_TXT,
    '          <h2 class="post-title"><a href="%s.html">%s</a></h2>' % (SLUG, TITULO.replace('&', '&amp;')),
    '          <p class="post-excerpt">%s</p>' % EXTRACTO,
    '          <p class="post-meta"><span data-i18n="read-time">Tiempo de lectura</span>: 4 min</p>',
    '          <a class="post-more" href="%s.html"><span data-i18n="read-more">Leer más →</span></a>' % SLUG,
    '        </div>',
    '      </article>'])
blog2 = blog.replace(cierre, cierre + NLB + NLB + tarjeta)
wr('blog.html', blog2)
n1 = len(re.findall(r'<article class="post-card', blog2))
check('las tarjetas pasan de %d a %d' % (n0, n0 + 1), n1 == n0 + 1, '(ahora %d)' % n1)
check('el slug nuevo aparece 2 veces (titulo y boton)', blog2.count('href="%s.html"' % SLUG) == 2)
check('no hay modales', 'modal-overlay' not in blog2)
check('blog.html termina en </body></html>', re.search(r'</body>\s*</html>\s*$', blog2) is not None)
ok, info = balanced(blog2)
check('blog.html sigue bien formado', ok, '' if ok else str(info))
last = re.findall(r'<article class="post-card[^>]*data-date="([^"]+)"', blog2)[-1]
check('la ultima tarjeta es la nueva', last == FECHA_ISO)

# ---------------------------------------------------------------- blog.md
print('\n[5] blog.md')
NLM = '\r\n' if '\r\n' in md0 else '\n'
lines = md0.split(NLM)
idx = next(i for i, l in enumerate(lines) if re.match(r'^1\. \*\*\[', l))
entrada = ['1. **[%s] %s — %s.** %s' % (CAT_TXT, FECHA_TXT, TITULO, EXTRACTO),
           '   Leer: https://pulidotax.com/%s.html' % SLUG, '']
# renumerar el resto
resto = []
for l in lines[idx:]:
    m = re.match(r'^(\d+)(\. \*\*\[.*)$', l)
    resto.append('%d%s' % (int(m.group(1)) + 1, m.group(2)) if m else l)
md2 = NLM.join(lines[:idx] + entrada + resto)
wr('blog.md', md2)
e1 = len(re.findall(r'(?m)^\d+\. \*\*\[', md2))
check('entradas de blog.md: %d -> %d' % (e0, e0 + 1), e1 == e0 + 1, '(ahora %d)' % e1)
nums = [int(x) for x in re.findall(r'(?m)^(\d+)\. \*\*\[', md2)]
check('la numeracion es 1..N sin huecos ni repetidos', nums == list(range(1, len(nums) + 1)))
check('cada entrada tiene su linea "Leer:"', len(re.findall(r'Leer: https://pulidotax\.com/', md2)) == e1)

# ---------------------------------------------------------------- sitemap
print('\n[6] sitemap.xml')
sm = rd('sitemap.xml')
marca = '<!-- Articulos del blog, del mas reciente al mas antiguo -->'
check('el comentario ancla aparece una vez', sm.count(marca) == 1)
NLS = '\r\n' if '\r\n' in sm else '\n'
bloque = NLS.join(['  <url>', '    <loc>https://pulidotax.com/%s.html</loc>' % SLUG, '    <lastmod>%s</lastmod>' % FECHA_ISO, '  </url>'])
sm2 = sm.replace(marca, marca + NLS + bloque)
wr('sitemap.xml', sm2)
try:
    xml.dom.minidom.parseString(sm2.encode('utf-8'))
    okx = True
except Exception as e:
    okx = False; print('     XML invalido:', e)
n_urls = sm2.count('<loc>')
check('sitemap sigue siendo XML valido', okx)
check('el sitemap pasa de %d a %d URLs' % (sm.count('<loc>'), sm.count('<loc>') + 1), n_urls == sm.count('<loc>') + 1)
primera = re.findall(r'<loc>https://pulidotax\.com/([a-z0-9-]+)\.html</loc>', sm2)
check('el articulo nuevo es el primero de los articulos', SLUG in primera and primera.index(SLUG) == primera.index(next(s for s in primera if s not in ('servicios','sobre-mi','calculadora','sales-tax','blog','contacto'))))

# ---------------------------------------------------------------- enlaces internos
print('\n[7] ENLACES INTERNOS EN LA COPIA')
rotos = []
for f in os.listdir(TMP):
    if f.endswith('.html'):
        for h in set(re.findall(r'href="([a-z0-9-]+\.html)"', rd(f))):
            if not os.path.exists(os.path.join(TMP, h)):
                rotos.append((f, h))
check('ningun enlace roto en todo el sitio (copia)', not rotos, str(rotos[:3]))

print('\n' + ('=' * 70))
print('RESULTADO: %s' % ('TODO CORRECTO' if not fails else '%d COMPROBACIONES FALLAN: %s' % (len(fails), fails)))
