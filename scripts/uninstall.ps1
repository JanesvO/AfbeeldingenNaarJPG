param([switch]$RemoveSettings)

$appName = "Afbeeldingen Naar JPG"
$installDir = Join-Path $env:LOCALAPPDATA "Programs\AfbeeldingenNaarJPG"
$configDir = Join-Path $env:APPDATA "AfbeeldingenNaarJPG"

Get-Process -Name "AfbeeldingenNaarJPG" -ErrorAction SilentlyContinue | Stop-Process -Force

foreach ($shortcut in @(
    (Join-Path ([Environment]::GetFolderPath("Programs")) "$appName.lnk"),
    (Join-Path ([Environment]::GetFolderPath("Desktop")) "$appName.lnk")
)) {
    if (Test-Path -LiteralPath $shortcut) { Remove-Item -LiteralPath $shortcut -Force }
}

Remove-Item -Path "HKCU:\Software\Microsoft\Windows\CurrentVersion\Uninstall\AfbeeldingenNaarJPG" -Recurse -Force -ErrorAction SilentlyContinue

if ($RemoveSettings -and (Test-Path -LiteralPath $configDir)) {
    Remove-Item -LiteralPath $configDir -Recurse -Force
}

# Dit script staat zelf in de installatiemap; verwijder die vanuit een los proces.
if (Test-Path -LiteralPath $installDir) {
    Start-Process -WindowStyle Hidden -FilePath "cmd.exe" -ArgumentList "/c timeout /t 2 >nul & rmdir /s /q `"$installDir`""
}

Write-Host "$appName is verwijderd. Je geconverteerde afbeeldingen blijven gewoon staan."
