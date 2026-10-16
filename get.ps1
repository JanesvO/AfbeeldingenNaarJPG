# Downloadt de nieuwste versie van Afbeeldingen Naar JPG en installeert die.
# Gebruik:  irm https://raw.githubusercontent.com/JanesvO/AfbeeldingenNaarJPG/main/get.ps1 | iex
param([Parameter(ValueFromRemainingArguments = $true)][string[]]$InstallerArguments)

$ErrorActionPreference = "Stop"
[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12

$zipUrl = "https://github.com/JanesvO/AfbeeldingenNaarJPG/releases/latest/download/AfbeeldingenNaarJPG.zip"
$workDir = Join-Path $env:TEMP ("afbeeldingen-naar-jpg-" + [guid]::NewGuid().ToString("N").Substring(0, 8))
$zipPath = Join-Path $workDir "AfbeeldingenNaarJPG.zip"

New-Item -ItemType Directory -Force -Path $workDir | Out-Null
try {
    Write-Host "Afbeeldingen Naar JPG downloaden..."
    $ProgressPreference = "SilentlyContinue"  # maakt Invoke-WebRequest in Windows PowerShell veel sneller
    Invoke-WebRequest -Uri $zipUrl -OutFile $zipPath -UseBasicParsing
    Expand-Archive -LiteralPath $zipPath -DestinationPath $workDir -Force
    $installer = Get-ChildItem -LiteralPath $workDir -Directory |
        ForEach-Object { Join-Path $_.FullName "scripts\install.ps1" } |
        Where-Object { Test-Path -LiteralPath $_ } |
        Select-Object -First 1
    if (-not $installer) { throw "install.ps1 niet gevonden in de download." }

    & powershell.exe -ExecutionPolicy Bypass -NoProfile -File $installer @InstallerArguments
    if ($LASTEXITCODE -ne 0) { throw "De installatie is mislukt (exitcode $LASTEXITCODE)." }
} finally {
    Remove-Item -LiteralPath $workDir -Recurse -Force -ErrorAction SilentlyContinue
}
