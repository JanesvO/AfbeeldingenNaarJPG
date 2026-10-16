<#
.SYNOPSIS
    Bouwt Afbeeldingen Naar JPG als zelfstandige Windows-app en publiceert die optioneel.

.DESCRIPTION
    - Bouwt in een eigen, schone omgeving (.venv-build), zodat er geen overbodige packages meekomen.
    - Maakt dist\AfbeeldingenNaarJPG-<versie>.zip met Install.cmd, scripts\ en app\ (de exe).
    - Met -Publish: maakt een GitHub-release met AfbeeldingenNaarJPG.zip (vaste naam, zodat
      .../releases/latest/download/AfbeeldingenNaarJPG.zip altijd de nieuwste versie geeft).
#>
param([switch]$Publish)

$ErrorActionPreference = "Stop"

$projectRoot = Split-Path -Parent $PSScriptRoot
$venv = Join-Path $projectRoot ".venv-build"
$python = Join-Path $venv "Scripts\python.exe"
$buildRoot = Join-Path $projectRoot "build"
$distRoot = Join-Path $projectRoot "dist"
$stage = Join-Path $distRoot "AfbeeldingenNaarJPG"
$repo = "JanesvO/AfbeeldingenNaarJPG"

function Assert-ExitCode([string]$What) {
    if ($LASTEXITCODE -ne 0) { throw "$What is mislukt (exitcode $LASTEXITCODE)." }
}

if (-not (Test-Path -LiteralPath $python)) {
    Write-Host "Bouwomgeving maken (.venv-build)"
    & py -3.12 -m venv $venv
    Assert-ExitCode "Bouwomgeving maken"
}
& $python -m pip install --quiet --disable-pip-version-check -r (Join-Path $projectRoot "requirements.txt") pyinstaller
Assert-ExitCode "Packages installeren"

$version = (& $python -c "import sys; sys.path.insert(0, r'$projectRoot\src'); import afbeeldingen_naar_jpg as a; print(a.__version__)").Trim()
Assert-ExitCode "Versie bepalen"
Write-Host "Bouwen: Afbeeldingen Naar JPG $version"

foreach ($folder in $buildRoot, $stage) {
    if (Test-Path -LiteralPath $folder) { Remove-Item -LiteralPath $folder -Recurse -Force }
}
New-Item -ItemType Directory -Force -Path $buildRoot | Out-Null

# Versie-informatie voor de exe (zichtbaar bij Eigenschappen > Details en in Apps).
$parts = @($version.Split(".") + @("0", "0", "0", "0"))[0..3] -join ", "
$versionFile = Join-Path $buildRoot "version_info.txt"
@"
VSVersionInfo(
  ffi=FixedFileInfo(filevers=($parts), prodvers=($parts)),
  kids=[
    StringFileInfo([StringTable('041304B0', [
      StringStruct('CompanyName', 'JvO ICT'),
      StringStruct('FileDescription', 'Afbeeldingen Naar JPG'),
      StringStruct('FileVersion', '$version'),
      StringStruct('ProductName', 'Afbeeldingen Naar JPG'),
      StringStruct('ProductVersion', '$version'),
      StringStruct('LegalCopyright', 'JvO ICT')])]),
    VarFileInfo([VarStruct('Translation', [1043, 1200])])
  ]
)
"@ | Set-Content -LiteralPath $versionFile -Encoding ASCII

$icon = Join-Path $projectRoot "assets\icon.ico"
& $python -m PyInstaller `
    --noconfirm --clean --windowed `
    --name AfbeeldingenNaarJPG `
    --icon $icon `
    --add-data "$icon;." `
    --version-file $versionFile `
    --paths (Join-Path $projectRoot "src") `
    --collect-all pillow_heif `
    --distpath (Join-Path $buildRoot "dist") `
    --workpath (Join-Path $buildRoot "work") `
    --specpath $buildRoot `
    (Join-Path $projectRoot "launcher.py")
Assert-ExitCode "PyInstaller"

# Pakket samenstellen.
New-Item -ItemType Directory -Force -Path (Join-Path $stage "scripts") | Out-Null
Move-Item -LiteralPath (Join-Path $buildRoot "dist\AfbeeldingenNaarJPG") -Destination (Join-Path $stage "app")
Copy-Item -LiteralPath (Join-Path $PSScriptRoot "Install.cmd") -Destination $stage
Copy-Item -LiteralPath (Join-Path $PSScriptRoot "install.ps1") -Destination (Join-Path $stage "scripts")
Copy-Item -LiteralPath (Join-Path $PSScriptRoot "uninstall.ps1") -Destination (Join-Path $stage "scripts")
@"
Afbeeldingen Naar JPG $version - JvO ICT (https://jvoict.nl/)

Installeren: dubbelklik op Install.cmd.
Handleiding: https://github.com/$repo#readme
"@ | Set-Content -LiteralPath (Join-Path $stage "LEESMIJ.txt") -Encoding UTF8

# Rooktest: de exe moet starten en blijven draaien.
$exe = Join-Path $stage "app\AfbeeldingenNaarJPG.exe"
$process = Start-Process -FilePath $exe -PassThru
Start-Sleep -Seconds 6
if ($process.HasExited) { throw "De app is direct afgesloten (exitcode $($process.ExitCode))." }
Stop-Process -Id $process.Id -Force
Write-Host "Rooktest OK: de app start."

$zipPath = Join-Path $distRoot "AfbeeldingenNaarJPG-$version.zip"
if (Test-Path -LiteralPath $zipPath) { Remove-Item -LiteralPath $zipPath -Force }
# Niet Compress-Archive: dat zet in Windows PowerShell 5.1 backslashes in de zip-paden.
& $python -c "import shutil, sys; shutil.make_archive(sys.argv[1][:-4], 'zip', sys.argv[2], 'AfbeeldingenNaarJPG')" $zipPath $distRoot
Assert-ExitCode "Zip maken"
$sizeMb = [math]::Round((Get-Item -LiteralPath $zipPath).Length / 1MB, 1)
Write-Host "Zip: $zipPath ($sizeMb MB)"

if (-not $Publish) { exit 0 }

$assetPath = Join-Path $distRoot "AfbeeldingenNaarJPG.zip"
Copy-Item -LiteralPath $zipPath -Destination $assetPath -Force
$notes = @"
**Download ``AfbeeldingenNaarJPG.zip`` hieronder**, pak uit en dubbelklik op ``Install.cmd``. De bestanden "Source code" heb je niet nodig.

Of installeer met een opdracht in PowerShell:

``````powershell
irm https://raw.githubusercontent.com/$repo/main/get.ps1 | iex
``````

Gratis te gebruiken. Gemaakt door [JvO ICT](https://jvoict.nl/).
"@
$notesPath = Join-Path $distRoot "release-notes.md"
[IO.File]::WriteAllText($notesPath, $notes, (New-Object Text.UTF8Encoding $false))
gh release create "v$version" $assetPath --repo $repo --title "Afbeeldingen Naar JPG $version" --notes-file $notesPath
Assert-ExitCode "GitHub-release maken"
Write-Host "Gepubliceerd: https://github.com/$repo/releases/tag/v$version"
