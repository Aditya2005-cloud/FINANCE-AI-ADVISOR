param(
    [switch]$Reload
)

$ErrorActionPreference = 'Stop'

$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
$backendDir = Join-Path $repoRoot 'backend'
$pserveExe = Join-Path $backendDir 'venv\Scripts\pserve.exe'
$iniPath = Join-Path $backendDir 'development.ini'

if (-not (Test-Path $backendDir)) {
    throw "Backend directory not found: $backendDir"
}

if (-not (Test-Path $pserveExe)) {
    throw "pserve not found at $pserveExe. Create backend venv and install dependencies first."
}

if (-not (Test-Path $iniPath)) {
    throw "development.ini not found at $iniPath"
}

Push-Location $backendDir
try {
    Write-Host "Starting backend on http://localhost:6543 ..." -ForegroundColor Cyan

    if ($Reload) {
        & $pserveExe 'development.ini' '--reload'
    }
    else {
        & $pserveExe 'development.ini'
    }
}
finally {
    Pop-Location
}
