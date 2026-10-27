# Genera PDF (2 páginas: frente y reverso) y PNG de cada lado con Edge sin pantalla.
$env:PATH = [Environment]::GetEnvironmentVariable("PATH","User") + ";" + [Environment]::GetEnvironmentVariable("PATH","Machine")
$root = $PSScriptRoot
python "$root\build.py"
$edge = "C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
$out = Join-Path $root "salida"
New-Item -ItemType Directory -Force -Path $out | Out-Null
$tmp = Join-Path $env:TEMP "tarjeta-edge-profile"
$common = @("--headless=new","--disable-gpu","--user-data-dir=$tmp","--no-pdf-header-footer")

foreach ($v in @(@("tarjeta","tarjeta-pulido-tax"), @("tarjeta-sangrado","tarjeta-pulido-tax-imprenta-sangrado"))) {
    $src = "file:///" + ((Resolve-Path "$root\$($v[0]).html").Path -replace '\\','/')
    & $edge @common "--print-to-pdf=$out\$($v[1]).pdf" $src 2>$null | Out-Null
}
# PNG de vista previa (frente y reverso), 4x. Frente arriba y reverso abajo.
$src = "file:///" + ((Resolve-Path "$root\tarjeta.html").Path -replace '\\','/')
& $edge @common "--hide-scrollbars" "--force-device-scale-factor=4" "--window-size=336,384" "--screenshot=$out\tarjeta-vista-previa.png" $src 2>$null | Out-Null
Get-ChildItem $out | Select-Object Name, Length
# Imagenes digitales: un PNG por lado (4x = 1344x768)
foreach ($lado in "frente","reverso") {
    $src = "file:///" + ((Resolve-Path "$root\tarjeta-$lado.html").Path -replace '\\','/')
    & $edge @common "--hide-scrollbars" "--force-device-scale-factor=4" "--window-size=336,192" "--screenshot=$out\tarjeta-digital-$lado.png" $src 2>$null | Out-Null
}
