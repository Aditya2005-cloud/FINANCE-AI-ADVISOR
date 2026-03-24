param(
    [switch]$Reload
)

$ErrorActionPreference = 'Stop'

$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
$backendDir = Join-Path $repoRoot 'backend'
$pythonExe = Join-Path $backendDir 'venv\Scripts\python.exe'

if (-not (Test-Path $backendDir)) {
    throw "Backend directory not found: $backendDir"
}

if (-not (Test-Path $pythonExe)) {
    throw "Python executable not found at $pythonExe. Create backend venv and install dependencies first."
}

Push-Location $backendDir
try {
    Write-Host "Starting FastAPI ML backend on http://localhost:8000 ..." -ForegroundColor Cyan

    if ($Reload) {
        & $pythonExe -m uvicorn finance_ai.fastapi_app:app --host 0.0.0.0 --port 8000 --reload
    }
    else {
        & $pythonExe -m uvicorn finance_ai.fastapi_app:app --host 0.0.0.0 --port 8000
    }
}
finally {
    Pop-Location
}
