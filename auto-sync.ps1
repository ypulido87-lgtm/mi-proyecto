$env:PATH = "C:\Program Files\Git\cmd;" + $env:PATH
$carpeta = "C:\Claude"
$watcher = New-Object System.IO.FileSystemWatcher
$watcher.Path = $carpeta
$watcher.IncludeSubdirectories = $true
$watcher.EnableRaisingEvents = $true

Write-Host "Monitoreando cambios en $carpeta... (Ctrl+C para detener)"

while ($true) {
    $cambio = $watcher.WaitForChanged([System.IO.WatcherChangeTypes]::All, 5000)
    if (-not $cambio.TimedOut) {
        $archivo = $cambio.Name
        if ($archivo -notmatch "\.git" -and $archivo -notmatch "auto-sync") {
            Write-Host "Cambio detectado: $archivo - Subiendo a GitHub..."
            Set-Location $carpeta
            git add .
            git commit -m "auto-sync: $archivo actualizado $(Get-Date -Format 'yyyy-MM-dd HH:mm')"
            git push
            Write-Host "Subido correctamente."
        }
    }
}
