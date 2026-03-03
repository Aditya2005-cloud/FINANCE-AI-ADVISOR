param(
    [switch]$Reload
)

$ErrorActionPreference = 'Stop'

$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
$backendScript = Join-Path $PSScriptRoot 'start-backend.ps1'
$frontendScript = Join-Path $PSScriptRoot 'start-frontend.ps1'

if (-not (Test-Path $backendScript)) {
    throw "Missing script: $backendScript"
}

if (-not (Test-Path $frontendScript)) {
    throw "Missing script: $frontendScript"
}

$backendCommand = if ($Reload) {
    "& '$backendScript' -Reload"
} else {
    "& '$backendScript'"
}

Write-Host "Launching backend in a new PowerShell window..." -ForegroundColor Cyan
Start-Process powershell -ArgumentList '-NoExit', '-ExecutionPolicy', 'Bypass', '-Command', $backendCommand | Out-Null

Write-Host "Starting frontend in current terminal..." -ForegroundColor Cyan
& $frontendScript
