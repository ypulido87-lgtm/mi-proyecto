# AEO & Agent Readiness Toolkit

Kit de Claude Code Agent Skills (de terceros, no de Pulido Tax) que audita un sitio web para AEO (Answer Engine Optimization) y "AI Agent Readiness" — qué tan bien pueden descubrir, leer y citar el sitio los agentes/IA.

**Movido aquí el 3 sep 2026** desde `C:\Users\yudit\Desktop\AEO Agent Readiness Toolkit\` (venía con una carpeta duplicada por el zip, ya aplanada).

## Instalación del skill (hecha 3 sep 2026)
Los 8 módulos de `.claude/skills/` se copiaron a `C:\Users\yudit\.claude\skills\` para que estén disponibles como skill de Claude Code en **cualquier proyecto**, no solo aquí:
`aeo-agent-readiness`, `aeo-answerability`, `aeo-bot-access`, `aeo-commerce-readiness`, `aeo-content-accessibility`, `aeo-discoverability`, `aeo-llms`, `aeo-protocol-discovery`.

**Estado: totalmente operativo (3 sep 2026).** El skill quedó activo de inmediato en Claude Code (sin reiniciar). Se instaló Python 3.12.10 vía `winget install Python.Python.3.12`. Validado: `validate_toolkit.py` confirma los 8 skills y sus scripts, `test_toolkit.py` pasa 124/124 aserciones.

**Detalle técnico — PATH:** el instalador sí agregó `C:\Users\yudit\AppData\Local\Programs\Python\Python312\` al PATH del usuario (antes de la carpeta WindowsApps que tenía el stub falso). Pero cualquier terminal/sesión de Claude Code que ya estuviera abierta ANTES de instalar Python no ve ese PATH nuevo hasta que se abra una terminal nueva — es normal en Windows, no es un problema de la instalación. Si `python --version` falla con el mensaje de "no se encontró Python, instalar desde Microsoft Store", es por esto: basta abrir una terminal nueva (o reiniciar Claude Code).

## Contenido
- `audits/` — auditorías previas guardadas para `acdamerica.net`, `culturaminiteka.com`, `its-ve.com`, `rosamariabello.com` (trabajo anterior, sitios de terceros/clientes).
- `reports/` — el último reporte generado (`.md` y `.json`) con su "previous" para comparación antes/después.
- `AEO-TOOLKIT.md`, `CLAUDE.md` — documentación del toolkit.

## Uso (una vez reiniciado Claude Code y con Python instalado)
Pedirle a Claude: *"Audita este sitio para AEO y AI Agent Readiness"* — el skill se activa solo. También se puede correr directo:
```bash
python .claude/skills/aeo-agent-readiness/scripts/aeo_audit.py --project . --url https://pulidotax.com
```

## Regla importante del propio toolkit
Nunca publica una señal falsa (MCP Server Card, OAuth, etc.) si la capacidad no existe de verdad, y pide aprobación explícita antes de tocar permisos de crawlers de IA, DNS, CDN/WAF, despliegue, o comercio/pagos.
