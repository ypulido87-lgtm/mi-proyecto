# Flyers — temporada de impuestos 2026–2027 (Pulido Tax & Accounting LLC)

Creados el 11 oct 2026. 3 versiones × 2 formatos, solo español, contacto por **QR a WhatsApp + pulidotax.com** (no se imprime teléfono ni email, respetando la regla de la dueña).

## Archivos listos (carpeta `salida\`)
| Versión | Imprimir (carta 8.5x11) | Redes (1080x1080) |
|---|---|---|
| General (servicios + cómo trabajamos) | `flyer-general-carta.pdf` | `flyer-general-cuadrado.png` |
| Personas / trabajadores por cuenta propia | `flyer-personas-carta.pdf` | `flyer-personas-cuadrado.png` |
| Pequeños negocios y LLC | `flyer-negocios-carta.pdf` | `flyer-negocios-cuadrado.png` |

`*-carta-preview.png` son vistas previas de los PDF (no para imprimir).

## Cómo regenerar / editar
- Textos y versiones: `build.py` (diccionario `VERSIONS`). Estilos: `assets\flyer.css`. Fuentes locales: `assets\fonts\`.
- Regenerar todo: `powershell -File render.ps1` (usa Edge sin pantalla; requiere Python con `segno`).
- QR: `assets\qr-whatsapp.svg` → `https://wa.me/16892708845?text=Hola, quiero información sobre mis impuestos` (si cambia el número o el mensaje, regenerar con segno y volver a renderizar).

## Reglas de contenido aplicadas
Sin teléfono/email impresos · sin "bilingüe" · sin testimonios · sin precios ni promesas de reembolso · sin llamarse CPA · textos tomados de los servicios del sitio · disclaimer informativo al pie de la versión carta.

## Pendiente de Yudit antes de imprimir
Escanear el QR con el celular desde la pantalla/impresión de prueba y confirmar que abre su WhatsApp.
