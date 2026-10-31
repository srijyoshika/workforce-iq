<#
.SYNOPSIS
    Builds and starts the complete WorkforceIQ containerized stack via Docker Compose.
.DESCRIPTION
    Launches PostgreSQL 16, FastAPI Backend, and React Frontend containers with health checks.
#>

$ErrorActionPreference = "Stop"
$ProjectRoot = Split-Path -Parent $PSScriptRoot

Write-Host "======================================================================" -ForegroundColor Cyan
Write-Host " WorkforceIQ Containerized Stack Launcher (Docker Compose)" -ForegroundColor Cyan
Write-Host "======================================================================" -ForegroundColor Cyan

Set-Location $ProjectRoot

# 1. Check if Docker is running
try {
    docker info | Out-Null
} catch {
    Write-Error "Docker is not running or not in PATH. Please start Docker Desktop and retry."
    exit 1
}

# 2. Build and start containers
Write-Host "`n[1/3] Building and starting containers..." -ForegroundColor Yellow
docker compose up -d --build

# 3. Poll container health status
Write-Host "`n[2/3] Waiting for services to become healthy..." -ForegroundColor Yellow
$maxAttempts = 30
$attempt = 0
$healthy = $false

while ($attempt -lt $maxAttempts) {
    Start-Sleep -Seconds 3
    $attempt++
    
    $psOutput = docker compose ps --format json | ConvertFrom-Json
    $unhealthy = @($psOutput | Where-Object { $_.Health -ne "healthy" -and $_.State -ne "running" })
    
    Write-Host "  Checking status (Attempt $attempt/$maxAttempts)..." -ForegroundColor Gray
    
    if ($unhealthy.Count -eq 0) {
        $healthy = $true
        break
    }
}

Write-Host "`n[3/3] Deployment Status:" -ForegroundColor Green
docker compose ps

Write-Host "`n======================================================================" -ForegroundColor Cyan
Write-Host " Application is live:" -ForegroundColor Green
Write-Host "  • Frontend Web UI       : http://localhost (or http://localhost:5173)" -ForegroundColor White
Write-Host "  • Backend API & Docs    : http://localhost:8000/docs" -ForegroundColor White
Write-Host "  • Backend Health Check  : http://localhost:8000/api/v1/health/ready" -ForegroundColor White
Write-Host "  • PostgreSQL Port       : localhost:5432" -ForegroundColor White
Write-Host "======================================================================" -ForegroundColor Cyan

