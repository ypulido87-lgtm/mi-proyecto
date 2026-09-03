# Mi Proyecto

Repositorio de trabajo de Claude Code. Se sincroniza automáticamente a GitHub con `auto-sync.ps1`.

## Estructura

- `projects/` — un subcarpeta por proyecto activo:
  - `pulidotax-website/` — sitio web de Pulido Tax & Accounting LLC (pulidotax.com). El código que realmente se sube al servidor vive en `C:\Users\yudit\Downloads\sitio-pulidotax\`, no aquí — ver `NOTES.md` de esa carpeta.
  - `pulidotax-linkedin/` — transformación del perfil de LinkedIn de Pulido Tax.
- `auto-sync.ps1`, `claude.bat`, `iniciar-claude.ps1`, `claude.exe` — herramientas para lanzar Claude Code y sincronizar cambios con GitHub.

Cada carpeta de proyecto tiene su propio `NOTES.md` con el estado actual y un enlace a la memoria completa de Claude para ese proyecto.
