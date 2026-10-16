# Start de app vanuit de broncode (maakt zo nodig eerst .venv-build aan).
$projectRoot = Split-Path -Parent $PSScriptRoot
$python = Join-Path $projectRoot ".venv-build\Scripts\python.exe"
if (-not (Test-Path -LiteralPath $python)) {
    & py -3.12 -m venv (Join-Path $projectRoot ".venv-build")
    & $python -m pip install --quiet -r (Join-Path $projectRoot "requirements.txt")
}
$env:PYTHONPATH = Join-Path $projectRoot "src"
& $python -m afbeeldingen_naar_jpg
exit $LASTEXITCODE
