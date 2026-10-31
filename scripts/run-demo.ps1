<#
.SYNOPSIS
    Runs the WorkforceIQ executive demonstration script.
#>

$ErrorActionPreference = "Stop"
$ProjectRoot = Split-Path -Parent $PSScriptRoot

Write-Host "======================================================================" -ForegroundColor Cyan
Write-Host " Launching WorkforceIQ Executive End-to-End Demonstration" -ForegroundColor Cyan
Write-Host "======================================================================" -ForegroundColor Cyan

$env:PYTHONPATH = "$ProjectRoot/backend;$ProjectRoot"
& "$ProjectRoot/backend/venv/Scripts/python.exe" "$ProjectRoot/scripts/demo_scenario.py"

