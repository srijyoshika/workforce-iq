<#
.SYNOPSIS
    Runs the backend test suite with Pytest and HTTPX.
#>

$ErrorActionPreference = "Stop"
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectRoot = Split-Path -Parent $ScriptDir
$BackendDir = Join-Path $ProjectRoot "backend"
$VenvPython = Join-Path $BackendDir "venv\Scripts\python.exe"

Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host " WorkforceIQ - Executing Backend Test Suite               " -ForegroundColor Cyan
Write-Host "==========================================================" -ForegroundColor Cyan

$env:PYTHONPATH = "$ProjectRoot;$BackendDir"
Set-Location $BackendDir

& $VenvPython -m pytest tests -v --tb=short

