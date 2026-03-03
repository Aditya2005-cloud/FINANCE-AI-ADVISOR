$ErrorActionPreference = 'Stop'

$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
$backendDir = Join-Path $repoRoot 'backend'
$frontendDir = Join-Path $repoRoot 'frontend'
$pythonExe = Join-Path $backendDir 'venv\Scripts\python.exe'

Write-Host 'Running project checks...' -ForegroundColor Cyan

if (-not (Test-Path $pythonExe)) {
    throw "Python executable not found at $pythonExe"
}

Push-Location $backendDir
try {
    & $pythonExe -c "import finance_ai; print('backend import ok')"

    $testFiles = @(Get-ChildItem -Path (Join-Path $backendDir 'tests') -Recurse -File -Filter 'test*.py' -ErrorAction SilentlyContinue)
    if ($testFiles.Count -gt 0) {
        $pytestInstalled = (& $pythonExe -c "import importlib.util; print(importlib.util.find_spec('pytest') is not None)").Trim()

        if ($pytestInstalled -eq 'True') {
            & $pythonExe -m pytest
        }
        else {
            Write-Host 'pytest not installed; running unittest discovery instead.' -ForegroundColor Yellow
            & $pythonExe -m unittest discover -s tests -p 'test*.py' -v
        }
    }
    else {
        Write-Host 'No backend tests found in backend/tests (skipped backend test run).' -ForegroundColor Yellow
    }
}
finally {
    Pop-Location
}

Push-Location $frontendDir
try {
    npm run lint
    npm run build
}
finally {
    Pop-Location
}

Write-Host 'Checks completed.' -ForegroundColor Green
