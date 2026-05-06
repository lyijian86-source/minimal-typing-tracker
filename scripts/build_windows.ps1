param(
    [switch]$SkipTests
)

$ErrorActionPreference = "Stop"

$Root = Split-Path -Parent $PSScriptRoot
$VenvPython = Join-Path $Root ".venv\Scripts\python.exe"
$Python = if (Test-Path $VenvPython) { $VenvPython } else { "python" }

Set-Location $Root

if (-not $SkipTests) {
    & $Python -m pytest
}

& $Python -m PyInstaller --clean --noconfirm TypeLedger.spec

$Exe = Join-Path $Root "dist\TypeLedger\TypeLedger.exe"
if (-not (Test-Path $Exe)) {
    throw "Build completed, but TypeLedger.exe was not found at $Exe"
}

$Zip = Join-Path $Root "dist\TypeLedger-windows-portable.zip"
Compress-Archive -Path (Join-Path $Root "dist\TypeLedger\*") -DestinationPath $Zip -Force

Write-Host "Built: $Exe"
Write-Host "Packaged: $Zip"
