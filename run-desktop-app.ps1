$projectRoot = $PSScriptRoot
$venvPython = Join-Path $projectRoot ".venv\Scripts\python.exe"

if (-not (Test-Path -LiteralPath $venvPython)) {
    Write-Error "Geen ontwikkelomgeving gevonden. Voor normaal gebruik start je de standalone release in .\\release\\0.1\\"
    exit 1
}

& $venvPython (Join-Path $projectRoot "desktop_app.py")
exit $LASTEXITCODE
