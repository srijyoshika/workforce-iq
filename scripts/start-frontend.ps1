<#
.SYNOPSIS
    Starts the WorkforceIQ React + Vite frontend development server.
.DESCRIPTION
    Checks node_modules and boots Vite dev server on http://localhost:5173.
#>

$ErrorActionPreference = "Stop"
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectRoot = Split-Path -Parent $ScriptDir
$FrontendDir = Join-Path $ProjectRoot "frontend"

Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host " WorkforceIQ - Starting React + Vite Frontend             " -ForegroundColor Cyan
Write-Host "==========================================================" -ForegroundColor Cyan

Set-Location $FrontendDir

if (-not (Test-Path (Join-Path $FrontendDir "node_modules"))) {
    Write-Host "node_modules not found. Running npm install..." -ForegroundColor Yellow
    npm install
}

Write-Host "Starting Vite development server on http://localhost:5173..." -ForegroundColor Green
Write-Host "Proxy configured for /api -> http://127.0.0.1:8000" -ForegroundColor Gray
Write-Host "Press Ctrl+C to terminate." -ForegroundColor Gray

npm run dev

