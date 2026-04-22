param(
    [string]$PythonPath
)

Write-Host "Let op: dit is de ontwikkelroute met Python."
Write-Host "Voor normaal gebruik op een pc zonder Python gebruik je:"
Write-Host "  .\release\0.1\Install-AfbeeldingenNaarJPG-Standalone.cmd"
Write-Host ""

$projectRoot = $PSScriptRoot
$venvPath = Join-Path $projectRoot ".venv"
$venvPython = Join-Path $venvPath "Scripts\python.exe"
$startCmdPath = Join-Path $projectRoot "Start-AfbeeldingenNaarJPG.cmd"
$tempPath = Join-Path $projectRoot ".tmp"

function Invoke-Python {
    param(
        [string[]]$CommandParts,
        [Parameter(ValueFromRemainingArguments = $true)]
        [string[]]$Arguments
    )

    & $CommandParts[0] @($CommandParts | Select-Object -Skip 1) @Arguments
}

function Resolve-PythonCommand {
    param(
        [string]$PreferredPath
    )

    if ($PreferredPath) {
        if (Test-Path -LiteralPath $PreferredPath) {
            return @($PreferredPath)
        }
        Write-Error "Python niet gevonden op opgegeven pad: $PreferredPath"
        exit 1
    }

    $pythonCommand = Get-Command python -ErrorAction SilentlyContinue
    if ($pythonCommand) {
        return @($pythonCommand.Source)
    }

    $pyLauncher = Get-Command py -ErrorAction SilentlyContinue
    if ($pyLauncher) {
        return @($pyLauncher.Source, "-3")
    }

    $winget = Get-Command winget -ErrorAction SilentlyContinue
    if (-not $winget) {
        Write-Error "Python ontbreekt en winget is niet beschikbaar. Installeer Python 3.11+ handmatig."
        exit 1
    }

    Write-Host "Python ontbreekt. Installatie via winget wordt gestart..."
    & $winget.Source install --id Python.Python.3.12 --exact --accept-package-agreements --accept-source-agreements
    if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

    $pythonCommand = Get-Command python -ErrorAction SilentlyContinue
    if ($pythonCommand) {
        return @($pythonCommand.Source)
    }

    $pyLauncher = Get-Command py -ErrorAction SilentlyContinue
    if ($pyLauncher) {
        return @($pyLauncher.Source, "-3")
    }

    Write-Error "Python is geinstalleerd, maar nog niet beschikbaar in deze sessie. Open PowerShell opnieuw en probeer opnieuw."
    exit 1
}

$pythonCommand = Resolve-PythonCommand -PreferredPath $PythonPath

New-Item -ItemType Directory -Force -Path $tempPath | Out-Null
$env:TEMP = $tempPath
$env:TMP = $tempPath

Write-Host "Stap 1/4 - Virtuele omgeving maken"
Invoke-Python $pythonCommand -m venv $venvPath
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

if (-not (Test-Path -LiteralPath $venvPython)) {
    Write-Error "De virtuele omgeving is niet goed aangemaakt."
    exit 1
}

Write-Host "Stap 2/4 - Pip bijwerken"
& $venvPython -m pip install --upgrade pip
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

Write-Host "Stap 3/4 - Requirements installeren"
& $venvPython -m pip install -r (Join-Path $projectRoot "requirements.txt")
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

Write-Host "Stap 4/4 - Startbestand aanmaken"
$cmdContent = @"
@echo off
setlocal
set "PROJECT_ROOT=%~dp0"
"%PROJECT_ROOT%.venv\Scripts\python.exe" "%PROJECT_ROOT%desktop_app.py"
endlocal
"@
Set-Content -LiteralPath $startCmdPath -Value $cmdContent -Encoding ASCII

Write-Host ""
Write-Host "Installatie voltooid."
Write-Host "Start de app via:"
Write-Host "  $startCmdPath"

exit 0
