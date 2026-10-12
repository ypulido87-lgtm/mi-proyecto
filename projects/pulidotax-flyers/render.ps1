# Genera PDF (carta) y PNG (cuadrado + vista previa de carta) con Edge sin pantalla.
$env:PATH = [Environment]::GetEnvironmentVariable("PATH","User") + ";" + [Environment]::GetEnvironmentVariable("PATH","Machine")
$root = $PSScriptRoot
python "$root\build.py"
$edge = "C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
$out = Join-Path $root "salida"
New-Item -ItemType Directory -Force -Path $out | Out-Null
$tmp = Join-Path $env:TEMP "flyer-edge-profile"

foreach ($v in "general","personas","negocios") {
    $carta = (Resolve-Path "$root\html\$v-carta.html").Path
    $cuad  = (Resolve-Path "$root\html\$v-cuadrado.html").Path
    # PDF carta para imprimir
    & $edge --headless=new --disable-gpu --user-data-dir=$tmp --no-pdf-header-footer --print-to-pdf="$out\flyer-$v-carta.pdf" "file:///$($carta -replace '\\','/')" 2>$null | Out-Null
    # PNG carta (vista previa, 2x)
    & $edge --headless=new --disable-gpu --user-data-dir=$tmp --hide-scrollbars --force-device-scale-factor=2 --window-size=816,1056 --screenshot="$out\flyer-$v-carta-preview.png" "file:///$($carta -replace '\\','/')" 2>$null | Out-Null
    # PNG cuadrado para redes
    & $edge --headless=new --disable-gpu --user-data-dir=$tmp --hide-scrollbars --force-device-scale-factor=1 --window-size=1080,1080 --screenshot="$out\flyer-$v-cuadrado.png" "file:///$($cuad -replace '\\','/')" 2>$null | Out-Null
}
Get-ChildItem $out | Select-Object Name, Length
