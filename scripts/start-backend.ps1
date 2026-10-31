<#
.SYNOPSIS
    Starts the WorkforceIQ FastAPI backend application with auto-reload.
.DESCRIPTION
    Sets up the Python path, activates the virtual environment if present,
    and boots the Uvicorn ASGI server on http://127.0.0.1:8000.
#>

$ErrorActionPreference = "Stop"
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectRoot = Split-Path -Parent $ScriptDir
$BackendDir = Join-Path $ProjectRoot "backend"
$VenvPython = Join-Path $BackendDir "venv\Scripts\python.exe"

Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host " WorkforceIQ - Starting FastAPI Backend Server            " -ForegroundColor Cyan
Write-Host "==========================================================" -ForegroundColor Cyan

if (-not (Test-Path $VenvPython)) {
    Write-Warning "Python virtual environment not found at $VenvPython."
    Write-Host "Creating virtual environment and installing dependencies..." -ForegroundColor Yellow
    py -3.11 -m venv (Join-Path $BackendDir "venv")
    & $VenvPython -m pip install -r (Join-Path $BackendDir "requirements.txt")
}

$env:PYTHONPATH = "$ProjectRoot;$BackendDir"
Set-Location $BackendDir

Write-Host "Starting Uvicorn ASGI Server on http://127.0.0.1:8000..." -ForegroundColor Green
Write-Host "API Documentation available at: http://127.0.0.1:8000/docs" -ForegroundColor Gray
Write-Host "Press Ctrl+C to terminate." -ForegroundColor Gray

& $VenvPython -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload

