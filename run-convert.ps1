$projectRoot = $PSScriptRoot
$venvPython = Join-Path $projectRoot ".venv\Scripts\python.exe"

if (-not (Test-Path -LiteralPath $venvPython)) {
    Write-Error "Geen virtuele omgeving gevonden. Maak eerst .venv aan en installeer requirements."
    exit 1
}

& $venvPython (Join-Path $projectRoot "src\convert_to_jpg.py") `
    --input (Join-Path $projectRoot "input")

exit $LASTEXITCODE
