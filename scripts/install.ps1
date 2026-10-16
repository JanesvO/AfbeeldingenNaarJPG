<#
.SYNOPSIS
    Installeert of werkt Afbeeldingen Naar JPG bij voor de huidige gebruiker.

.DESCRIPTION
    Kopieert de app naar %LOCALAPPDATA%\Programs\AfbeeldingenNaarJPG, maakt snelkoppelingen
    en zet het programma in Instellingen > Apps. Geen Python of beheerdersrechten nodig.
    Opnieuw draaien is veilig: de bestaande installatie wordt vervangen, instellingen blijven.
#>
param(
    [string]$InstallDir = (Join-Path $env:LOCALAPPDATA "Programs\AfbeeldingenNaarJPG"),
    [switch]$NoDesktopShortcut
)

$ErrorActionPreference = "Stop"

$appName = "Afbeeldingen Naar JPG"
$exeName = "AfbeeldingenNaarJPG.exe"
$packageRoot = Split-Path -Parent $PSScriptRoot
$appSource = Join-Path $packageRoot "app"
$exePath = Join-Path $InstallDir $exeName
$uninstallKey = "HKCU:\Software\Microsoft\Windows\CurrentVersion\Uninstall\AfbeeldingenNaarJPG"

function New-Shortcut([string]$Path) {
    $shell = New-Object -ComObject WScript.Shell
    $shortcut = $shell.CreateShortcut($Path)
    $shortcut.TargetPath = $exePath
    $shortcut.WorkingDirectory = $InstallDir
    $shortcut.IconLocation = $exePath
    $shortcut.Description = "Afbeeldingen omzetten naar JPG"
    $shortcut.Save()
}

try {
    if (-not (Test-Path -LiteralPath (Join-Path $appSource $exeName))) {
        throw "Programmabestanden niet gevonden in $appSource. Pak de zip eerst helemaal uit."
    }

    $running = Get-Process -Name "AfbeeldingenNaarJPG" -ErrorAction SilentlyContinue
    if ($running) {
        Write-Host "$appName is nog geopend en wordt afgesloten..."
        $running | Stop-Process -Force
        Start-Sleep -Seconds 1
    }

    Write-Host "Programma plaatsen in $InstallDir"
    if (Test-Path -LiteralPath $InstallDir) { Remove-Item -LiteralPath $InstallDir -Recurse -Force }
    New-Item -ItemType Directory -Force -Path $InstallDir | Out-Null
    Copy-Item -Path (Join-Path $appSource "*") -Destination $InstallDir -Recurse -Force
    Copy-Item -LiteralPath (Join-Path $PSScriptRoot "uninstall.ps1") -Destination $InstallDir -Force

    Write-Host "Snelkoppelingen maken"
    New-Shortcut (Join-Path ([Environment]::GetFolderPath("Programs")) "$appName.lnk")
    if (-not $NoDesktopShortcut) {
        New-Shortcut (Join-Path ([Environment]::GetFolderPath("Desktop")) "$appName.lnk")
    }

    $version = (Get-Item -LiteralPath $exePath).VersionInfo.ProductVersion
    if (-not $version) { $version = "onbekend" }
    New-Item -Path $uninstallKey -Force | Out-Null
    Set-ItemProperty -Path $uninstallKey -Name DisplayName -Value $appName
    Set-ItemProperty -Path $uninstallKey -Name DisplayVersion -Value $version
    Set-ItemProperty -Path $uninstallKey -Name DisplayIcon -Value $exePath
    Set-ItemProperty -Path $uninstallKey -Name Publisher -Value "JvO ICT"
    Set-ItemProperty -Path $uninstallKey -Name URLInfoAbout -Value "https://jvoict.nl/"
    Set-ItemProperty -Path $uninstallKey -Name InstallLocation -Value $InstallDir
    Set-ItemProperty -Path $uninstallKey -Name UninstallString -Value "powershell.exe -ExecutionPolicy Bypass -NoProfile -File `"$(Join-Path $InstallDir 'uninstall.ps1')`""
    Set-ItemProperty -Path $uninstallKey -Name NoModify -Value 1 -Type DWord
    Set-ItemProperty -Path $uninstallKey -Name NoRepair -Value 1 -Type DWord

    Write-Host ""
    Write-Host "$appName $version is geinstalleerd." -ForegroundColor Green
    if ($NoDesktopShortcut) {
        Write-Host "Start het programma via het Startmenu."
    } else {
        Write-Host "Start het programma via het Startmenu of de snelkoppeling op het bureaublad."
    }
    exit 0
} catch {
    Write-Host ""
    Write-Host "Installatie mislukt: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}
