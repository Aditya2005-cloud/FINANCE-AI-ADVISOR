$ErrorActionPreference = 'Stop'

$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
$frontendDir = Join-Path $repoRoot 'frontend'

if (-not (Test-Path $frontendDir)) {
    throw "Frontend directory not found: $frontendDir"
}

Push-Location $frontendDir
try {
    if (-not (Test-Path (Join-Path $frontendDir 'node_modules'))) {
        throw "frontend/node_modules not found. Run 'npm install' in frontend first."
    }

    Write-Host "Starting frontend on http://localhost:5173 ..." -ForegroundColor Cyan
    npm run dev
}
finally {
    Pop-Location
}
