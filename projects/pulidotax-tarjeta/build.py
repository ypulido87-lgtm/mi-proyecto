"""Genera el HTML de la tarjeta (frente y reverso), con y sin sangrado.
Tarjeta US estándar 3.5x2 in (336x192 px a 96 dpi). Sangrado 0.125 in por lado."""
from pathlib import Path

ROOT = Path(__file__).parent
BLEED = 12  # px = 0.125 in

LOGO = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 480 120" class="logo">
<polygon points="60,4 112,60 60,116 8,60" fill="#1A4A72"/>
<polygon points="60,18 98,60 60,102 22,60" fill="none" stroke="#B87333" stroke-width="1.6"/>
<text x="60" y="72" text-anchor="middle" font-family="Cormorant Garamond, Georgia, serif" font-size="42" font-weight="600" fill="#FFFFFF" letter-spacing="1">P</text>
<text x="136" y="58" font-family="Cormorant Garamond, Georgia, serif" font-size="46" font-weight="600" fill="#FFFFFF" letter-spacing="5">PULIDO</text>
<line x1="136" y1="68" x2="472" y2="68" stroke="rgba(255,255,255,0.25)" stroke-width="1"/>
<text x="136" y="88" font-family="DM Sans, Helvetica, Arial, sans-serif" font-size="13" font-weight="400" fill="#B87333" letter-spacing="4">TAX &amp; ACCOUNTING · LLC</text>
</svg>"""

CSS = """
@page{size:%(w)dpx %(h)dpx;margin:0}
:root{--blue:#0D2B45;--blue-mid:#1A4A72;--gold:#B87333;--cream:#FDF6EE;--ink:#2B3A47;
--fd:'Cormorant Garamond',Georgia,serif;--fb:'DM Sans',system-ui,sans-serif}
*{margin:0;padding:0;box-sizing:border-box}
html,body{width:%(w)dpx;height:%(h)dpx;background:#fff;-webkit-print-color-adjust:exact;print-color-adjust:exact}
.side{width:%(w)dpx;height:%(h)dpx;position:relative;overflow:hidden;page-break-after:always;break-after:page}
.side:last-child{page-break-after:auto;break-after:auto}
.safe{position:absolute;left:%(b)dpx;top:%(b)dpx;width:336px;height:192px}
.front{background:var(--blue)}
.front::before{content:"";position:absolute;left:0;right:0;bottom:0;height:%(bar)dpx;background:var(--gold)}
.front .safe{display:flex;flex-direction:column;align-items:center;justify-content:center;gap:16px}
.front .logo{width:236px;display:block}
.front .tag{font-family:var(--fd);font-style:italic;font-weight:500;font-size:13px;color:#E8C9A5;letter-spacing:.03em}
.back{background:var(--cream)}
.back::before{content:"";position:absolute;left:0;top:0;bottom:0;width:%(bar2)dpx;background:var(--gold)}
.back .safe{display:flex;align-items:center;justify-content:space-between;padding:0 22px 0 26px}
.who h1{font-family:var(--fd);font-weight:700;font-size:25px;line-height:1;color:var(--blue)}
.who .role{font-weight:700;font-size:7px;letter-spacing:.18em;text-transform:uppercase;color:var(--gold);margin:5px 0 11px}
.who ul{list-style:none}
.who li{font-size:8.5px;line-height:1;color:var(--ink);padding-left:10px;position:relative;margin-bottom:5px}
.who li::before{content:"";position:absolute;left:0;top:1.5px;width:4px;height:4px;background:var(--gold);transform:rotate(45deg)}
.who .web{margin-top:10px;font-weight:700;font-size:8.5px;color:var(--blue);letter-spacing:.02em}
.who .web span{color:var(--gold)}
.qr{text-align:center;flex:none}
.qr .tile{width:92px;height:92px;background:#fff;border:1px solid #E9DCCB;border-radius:6px;padding:6px}
.qr img{width:100%%;height:100%%;display:block}
.qr p{margin-top:6px;font-size:6.5px;line-height:1.35;font-weight:500;color:var(--blue)}
"""

BODY = """<div class="side front"><div class="safe">
<div class="logo-wrap">%(logo)s</div>
<div class="tag">Contabilidad e impuestos en español</div>
</div></div>
<div class="side back"><div class="safe">
<div class="who">
<h1>Yudit Pulido</h1>
<div class="role">Contabilidad e impuestos</div>
<ul><li>Declaración de impuestos</li><li>Bookkeeping mensual</li><li>Contabilidad para LLC y Corp</li><li>Nómina (payroll)</li></ul>
<div class="web">pulidotax.com <span>·</span> Orlando, FL</div>
</div>
<div class="qr"><div class="tile"><img src="assets/qr-whatsapp.svg" alt="QR WhatsApp"></div><p>Escanee y escríbanos<br>por WhatsApp</p></div>
</div></div>"""


def build(name, bleed):
    b = BLEED if bleed else 0
    p = dict(w=336 + 2 * b, h=192 + 2 * b, b=b, bar=4 + b, bar2=4 + b)
    html = ('<!DOCTYPE html><html lang="es"><head><meta charset="utf-8"><title>Tarjeta Pulido Tax</title>'
            '<link rel="stylesheet" href="assets/fonts.css"><style>%s</style></head><body>%s</body></html>'
            % (CSS % p, BODY % dict(logo=LOGO)))
    (ROOT / name).write_text(html, encoding="utf-8")


build("tarjeta.html", False)
build("tarjeta-sangrado.html", True)
print("ok")
