param(
    [string]$PythonPath,
    [string]$ReleaseVersion = "0.1"
)

$projectRoot = $PSScriptRoot
$releaseRoot = Join-Path $projectRoot "release"
$releaseVersionRoot = Join-Path $releaseRoot $ReleaseVersion
$buildRoot = Join-Path $releaseRoot ".build\$ReleaseVersion"
$distRoot = Join-Path $releaseVersionRoot "standalone"
$tempPath = Join-Path $projectRoot ".tmp"
$hookDir = Join-Path $projectRoot "pyinstaller_hooks"

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

    Write-Error "Geen Python-installatie gevonden."
    exit 1
}

$pythonCommand = Resolve-PythonCommand -PreferredPath $PythonPath
$pythonExecutable = if ($pythonCommand -is [array]) { $pythonCommand[0] } else { $pythonCommand }
$pythonRoot = Split-Path -Parent $pythonExecutable
$tclLibrary = Join-Path $pythonRoot "tcl\tcl8.6"
$tkLibrary = Join-Path $pythonRoot "tcl\tk8.6"

New-Item -ItemType Directory -Force -Path $tempPath | Out-Null
$env:TEMP = $tempPath
$env:TMP = $tempPath
$env:TCL_LIBRARY = $tclLibrary
$env:TK_LIBRARY = $tkLibrary

Write-Host "Benodigde packages controleren"
Invoke-Python @($pythonExecutable) -m pip install Pillow pyinstaller
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

New-Item -ItemType Directory -Force -Path $buildRoot | Out-Null
New-Item -ItemType Directory -Force -Path $distRoot | Out-Null

Push-Location $projectRoot
& $pythonExecutable -m PyInstaller `
    --noconfirm `
    --windowed `
    --name AfbeeldingenNaarJPG `
    --workpath $buildRoot `
    --distpath $distRoot `
    --additional-hooks-dir $hookDir `
    --hidden-import tkinter `
    --add-data "$tclLibrary;_tcl_data" `
    --add-data "$tkLibrary;_tk_data" `
    --add-binary "$pythonRoot\DLLs\tcl86t.dll;." `
    --add-binary "$pythonRoot\DLLs\tk86t.dll;." `
    --add-binary "$pythonRoot\DLLs\_tkinter.pyd;." `
    desktop_app.py
$exitCode = $LASTEXITCODE
Pop-Location

if ($exitCode -ne 0) { exit $exitCode }

$startCmdPath = Join-Path $releaseVersionRoot "Start-AfbeeldingenNaarJPG.cmd"
$cmdContent = @"
@echo off
setlocal
set "RELEASE_ROOT=%~dp0"
start "" "%RELEASE_ROOT%standalone\AfbeeldingenNaarJPG\AfbeeldingenNaarJPG.exe"
exit /b 0
"@
Set-Content -LiteralPath $startCmdPath -Value $cmdContent -Encoding ASCII
Copy-Item -LiteralPath (Join-Path $projectRoot "install-standalone.ps1") -Destination (Join-Path $releaseVersionRoot "install-standalone.ps1") -Force
Copy-Item -LiteralPath (Join-Path $projectRoot "Install-AfbeeldingenNaarJPG-Standalone.cmd") -Destination (Join-Path $releaseVersionRoot "Install-AfbeeldingenNaarJPG-Standalone.cmd") -Force
$readmeSource = Join-Path $projectRoot "release\0.1\README.md"
$readmeDestination = Join-Path $releaseVersionRoot "README.md"
if ((Resolve-Path $readmeSource).Path -ne (Resolve-Path $readmeDestination).Path) {
    Copy-Item -LiteralPath $readmeSource -Destination $readmeDestination -Force
}

Write-Host ""
Write-Host "Standalone build voltooid."
Write-Host "Release-map:"
Write-Host "  $releaseVersionRoot"

exit 0
