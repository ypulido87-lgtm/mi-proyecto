# -*- coding: utf-8 -*-
"""Genera los flyers de Pulido Tax (3 versiones x carta + cuadrado) como HTML.
Uso: python build.py   ->  escribe html/*.html ; render.ps1 los convierte a PDF/PNG."""
import pathlib

ROOT = pathlib.Path(__file__).parent
(ROOT / "html").mkdir(exist_ok=True)

LOGO = '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 480 120" class="logo">
<polygon points="60,4 112,60 60,116 8,60" fill="#1A4A72"/>
<polygon points="60,18 98,60 60,102 22,60" fill="none" stroke="#B87333" stroke-width="1.6"/>
<text x="60" y="72" text-anchor="middle" font-family="Cormorant Garamond, Georgia, serif" font-size="42" font-weight="600" fill="#FFFFFF" letter-spacing="1">P</text>
<text x="136" y="58" font-family="Cormorant Garamond, Georgia, serif" font-size="46" font-weight="600" fill="#FFFFFF" letter-spacing="5">PULIDO</text>
<line x1="136" y1="68" x2="472" y2="68" stroke="rgba(255,255,255,0.25)" stroke-width="1"/>
<text x="136" y="88" font-family="DM Sans, Helvetica, Arial, sans-serif" font-size="13" font-weight="400" fill="#B87333" letter-spacing="4">TAX &amp; ACCOUNTING · LLC</text>
</svg>'''

ICONS = {
    "doc": '<path d="M14 3H6a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V9z"/><path d="M14 3v6h6M8 13h8M8 17h6"/>',
    "book": '<path d="M4 5a2 2 0 0 1 2-2h13v16H6a2 2 0 0 0-2 2z"/><path d="M4 21V5M9 8h6M9 12h6"/>',
    "building": '<path d="M5 21V5a1 1 0 0 1 1-1h8a1 1 0 0 1 1 1v16M15 9h3a1 1 0 0 1 1 1v11M3 21h18M9 8h2M9 12h2M9 16h2"/>',
    "people": '<circle cx="9" cy="8" r="3.2"/><path d="M3 20c0-3.3 2.7-6 6-6s6 2.7 6 6"/><path d="M16 5.2a3.2 3.2 0 0 1 0 5.6M18 14.5c1.8.8 3 2.5 3 5.5"/>',
    "check": '<circle cx="12" cy="12" r="9"/><path d="M8 12.5l2.7 2.7L16 9.5"/>',
    "shield": '<path d="M12 3l7 3v5c0 4.5-3 8-7 10-4-2-7-5.5-7-10V6z"/><path d="M9 12l2.2 2.2L15.5 10"/>',
    "briefcase": '<rect x="3" y="7" width="18" height="13" rx="2"/><path d="M9 7V5a2 2 0 0 1 2-2h2a2 2 0 0 1 2 2v2M3 13h18"/>',
}

def icon(name):
    return f'<svg viewBox="0 0 24 24" fill="none" stroke="#B87333" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round">{ICONS[name]}</svg>'

VERSIONS = {
    "general": {
        "kicker": "Temporada de impuestos 2026–2027",
        "title": "Llegue a la temporada de impuestos con todo en orden",
        "sub": "Contabilidad e impuestos en español para personas, trabajadores independientes y pequeños negocios en Florida.",
        "items": [
            ("doc", "Declaración de impuestos", "Personal o de negocio, buscando cada deducción legítima que le corresponda."),
            ("book", "Bookkeeping mensual", "Sus libros al día y conciliados, listos para cualquier decisión."),
            ("building", "Contabilidad para LLC y Corp", "Obligaciones de su empresa en Florida bajo control."),
            ("people", "Nómina (payroll)", "Pagos, retenciones y reportes federales y estatales en orden."),
        ],
        "check_title": None, "check": [],
        "steps": [("01", "Conversamos", "Una consulta gratuita para conocer su negocio y sus números."),
                  ("02", "Diseñamos su plan", "Un servicio a la medida, con precio claro desde el principio."),
                  ("03", "Usted crece", "Números claros, IRS al día y tiempo para lo que mejor sabe hacer.")],
    },
    "personas": {
        "kicker": "Declaración de impuestos 2026–2027",
        "title": "¿Trabaja por su cuenta? Prepare su declaración con tiempo",
        "sub": "Declaración personal y de trabajador independiente, con cada deducción legítima que le corresponda.",
        "items": [
            ("doc", "Declaración personal", "Preparada correctamente y a tiempo, sin sorpresas de último minuto."),
            ("briefcase", "Trabajadores independientes", "Freelancers, contratistas y dueños de LLC de un solo miembro."),
            ("shield", "Deducciones legítimas", "Revisamos sus gastos para aprovechar lo que sí le corresponde."),
            ("check", "Acompañamiento ante el IRS", "Si el IRS le escribe, no está solo: le ayudamos a responder."),
        ],
        "check_title": "Qué tener a mano",
        "check": ["Identificación y SSN o ITIN", "Formularios W-2 y 1099", "Ingresos y gastos del negocio, con recibos", "Estados de cuenta del año"],
        "note": "Llegar con los papeles en orden le ahorra tiempo, estrés y sorpresas de último minuto.",
    },
    "negocios": {
        "kicker": "Cierre de año y temporada 2026–2027",
        "title": "Su negocio listo para el cierre de año",
        "sub": "Libros al día, nómina correcta y las obligaciones de su LLC o corporación en Florida bajo control.",
        "items": [
            ("book", "Bookkeeping mensual", "Registro y conciliación de todas sus transacciones, mes a mes."),
            ("doc", "Declaración de negocio", "Preparación según el tipo de entidad, con soporte ante el IRS."),
            ("building", "LLC y Corp en Florida", "Annual Report del estado y reportes BOI cuando aplica."),
            ("people", "Nómina (payroll)", "Salarios, depósitos de impuestos, W-2 y 1099 al final del año."),
        ],
        "check_title": "Antes del cierre, reúna",
        "check": ["Estados de cuenta bancarios y de tarjetas", "Registro de ingresos y facturas de gastos", "Información de nómina", "Inventario, si aplica"],
        "note": "Con los libros al día, el cierre de año y la declaración dejan de ser una carrera.",
    },
}

FONTS = '<link rel="stylesheet" href="../assets/fonts.css"><link rel="stylesheet" href="../assets/flyer.css">'
QR = '<img src="../assets/qr-whatsapp.svg" alt="QR WhatsApp">'
PHOTO = '<img class="photo" src="../assets/yudit-pulido.png" alt="Yudit Pulido Blanco">'
DISCLAIMER = "Pulido Tax &amp; Accounting LLC · Orlando, Florida · Este material es informativo y no constituye asesoría legal ni fiscal personalizada."


def items_html(items):
    out = []
    for ic, t, d in items:
        out.append(f'<div class="card"><div class="ic">{icon(ic)}</div><div><h3>{t}</h3><p>{d}</p></div></div>')
    return "\n".join(out)


def check_html(v):
    if not v["check"]:
        return ""
    lis = "".join(f"<li>{c}</li>" for c in v["check"])
    return f'<div class="check"><h4>{v["check_title"]}</h4><ul>{lis}</ul></div>'


def note_html(v):
    return f'<p class="note">{v["note"]}</p>' if v.get("note") else ""


def steps_html(v):
    if not v.get("steps"):
        return ""
    cols = "".join(f'<div class="step"><b>{n}</b><div><h4>{t}</h4><p>{d}</p></div></div>' for n, t, d in v["steps"])
    return f'<div class="steps"><h4 class="steps-title">Cómo trabajamos</h4><div class="steps-row">{cols}</div></div>'


def letter(key, v):
    return f'''<!DOCTYPE html><html lang="es"><head><meta charset="utf-8"><title>Flyer {key} (carta)</title>{FONTS}</head>
<body class="letter"><div class="page">
<header><div class="logo-wrap">{LOGO}</div><div class="kicker">{v["kicker"]}</div></header>
<main>
<h1>{v["title"]}</h1>
<p class="sub">{v["sub"]}</p>
<div class="rule"></div>
<div class="grid">{items_html(v["items"])}</div>
{check_html(v)}{note_html(v)}{steps_html(v)}
</main>
<footer>
<div class="who">{PHOTO}<div><strong>Yudit Pulido Blanco</strong><span>Fundadora · +15 años de experiencia</span><span>Atención directa y en español</span></div></div>
<div class="offer"><em>Primera consulta</em><b>GRATUITA</b><span>Sin compromiso · Precio según su negocio</span></div>
<div class="qr"><div class="tile">{QR}</div><span>Escanee y escríbanos<br>por WhatsApp</span></div>
</footer>
<div class="bottom"><span>pulidotax.com</span><span>Orlando, FL · Remoto y presencial en toda Florida</span></div>
<p class="legal">{DISCLAIMER}</p>
</div></body></html>'''


def square(key, v):
    return f'''<!DOCTYPE html><html lang="es"><head><meta charset="utf-8"><title>Flyer {key} (cuadrado)</title>{FONTS}</head>
<body class="square"><div class="page">
<header><div class="logo-wrap">{LOGO}</div><div class="kicker">{v["kicker"]}</div></header>
<main>
<h1>{v["title"]}</h1>
<p class="sub">{v["sub"]}</p>
<div class="grid">{items_html(v["items"])}</div>
</main>
<footer>
<div class="offer"><em>Primera consulta</em><b>GRATUITA</b><span>Sin compromiso · Atención en español</span><i>pulidotax.com · Orlando, FL</i></div>
<div class="qr"><div class="tile">{QR}</div><span>Escanee y escríbanos<br>por WhatsApp</span></div>
</footer>
</div></body></html>'''


for key, v in VERSIONS.items():
    (ROOT / "html" / f"{key}-carta.html").write_text(letter(key, v), encoding="utf-8")
    (ROOT / "html" / f"{key}-cuadrado.html").write_text(square(key, v), encoding="utf-8")
print("HTML generados:", sorted(p.name for p in (ROOT / "html").glob("*.html")))
