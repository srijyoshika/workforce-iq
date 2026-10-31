<#
.SYNOPSIS
    Starts both the backend and frontend in production mode for native Windows testing.
#>

$ErrorActionPreference = "Stop"
$ProjectRoot = Split-Path -Parent $PSScriptRoot

Write-Host "======================================================================" -ForegroundColor Cyan
Write-Host " WorkforceIQ Local Production Runner" -ForegroundColor Cyan
Write-Host "======================================================================" -ForegroundColor Cyan

Set-Location $ProjectRoot

# 1. Build frontend bundle if needed
Write-Host "`n[1/3] Building production frontend bundle..." -ForegroundColor Yellow
Set-Location "$ProjectRoot/frontend"
npm run build

# 2. Start Backend
Write-Host "`n[2/3] Starting FastAPI backend on http://127.0.0.1:8000..." -ForegroundColor Yellow
$backendProcess = Start-Process -FilePath "$ProjectRoot/backend/venv/Scripts/python.exe" `
    -ArgumentList "-m uvicorn app.main:app --host 127.0.0.1 --port 8000 --app-dir `"$ProjectRoot/backend`"" `
    -PassThru

# 3. Start Frontend Preview
Write-Host "`n[3/3] Starting Frontend preview server on http://localhost:5173..." -ForegroundColor Yellow
$frontendProcess = Start-Process -FilePath "npx" `
    -ArgumentList "vite preview --port 5173" `
    -WorkingDirectory "$ProjectRoot/frontend" `
    -PassThru

Write-Host "`n======================================================================" -ForegroundColor Green
Write-Host " WorkforceIQ is active!" -ForegroundColor Green
Write-Host "  • Web Dashboard : http://localhost:5173" -ForegroundColor White
Write-Host "  • Swagger Docs  : http://127.0.0.1:8000/docs" -ForegroundColor White
Write-Host "  Press Ctrl+C or kill processes to stop." -ForegroundColor Gray
Write-Host "======================================================================" -ForegroundColor Green

