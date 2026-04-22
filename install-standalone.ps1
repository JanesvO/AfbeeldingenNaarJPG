param(
    [string]$SourceRoot = $PSScriptRoot,
    [string]$InstallDir = (Join-Path $env:LOCALAPPDATA "Programs\AfbeeldingenNaarJPG")
)

$SourceRoot = $SourceRoot.Trim('"')
$SourceRoot = [System.IO.Path]::GetFullPath($SourceRoot)
$standaloneSource = Join-Path $SourceRoot "standalone\AfbeeldingenNaarJPG"
$exePath = Join-Path $InstallDir "AfbeeldingenNaarJPG.exe"
$desktopShortcut = Join-Path ([Environment]::GetFolderPath("Desktop")) "Afbeeldingen Naar JPG.lnk"
$startMenuDir = Join-Path $env:APPDATA "Microsoft\Windows\Start Menu\Programs"
$startMenuShortcut = Join-Path $startMenuDir "Afbeeldingen Naar JPG.lnk"

if (-not (Test-Path -LiteralPath $standaloneSource)) {
    Write-Error "Standalone bronmap niet gevonden: $standaloneSource"
    exit 1
}

New-Item -ItemType Directory -Force -Path $InstallDir | Out-Null
Copy-Item -Path (Join-Path $standaloneSource "*") -Destination $InstallDir -Recurse -Force

if (-not (Test-Path -LiteralPath $exePath)) {
    Write-Error "Installatie mislukt: executable niet gevonden in $InstallDir"
    exit 1
}

$wshShell = New-Object -ComObject WScript.Shell

try {
    $desktopLink = $wshShell.CreateShortcut($desktopShortcut)
    $desktopLink.TargetPath = $exePath
    $desktopLink.WorkingDirectory = $InstallDir
    $desktopLink.IconLocation = $exePath
    $desktopLink.Save()
}
catch {
    Write-Warning "Bureaublad-snelkoppeling kon niet worden aangemaakt."
}

try {
    $startMenuLink = $wshShell.CreateShortcut($startMenuShortcut)
    $startMenuLink.TargetPath = $exePath
    $startMenuLink.WorkingDirectory = $InstallDir
    $startMenuLink.IconLocation = $exePath
    $startMenuLink.Save()
}
catch {
    Write-Warning "Startmenu-snelkoppeling kon niet worden aangemaakt."
}

Write-Host "Standalone installatie voltooid."
Write-Host "Geinstalleerd in:"
Write-Host "  $InstallDir"
Write-Host ""
Write-Host "Je kunt het programma nu starten via het bureaublad, het startmenu of direct via:"
Write-Host "  $exePath"

exit 0
