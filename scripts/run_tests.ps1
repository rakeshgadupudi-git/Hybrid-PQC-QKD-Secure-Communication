<#
.SYNOPSIS
    Run the project test suite.

.DESCRIPTION
    Activates the virtual environment and runs pytest.
#>

$ErrorActionPreference = "Stop"
$ProjectRoot = Split-Path -Parent $PSScriptRoot
$VenvPython = Join-Path $ProjectRoot ".venv\Scripts\python.exe"

if (-not (Test-Path $VenvPython)) {
    Write-Error "Virtual environment not found. Run setup first."
    exit 1
}

Write-Host "Running tests..." -ForegroundColor Cyan
& $VenvPython -m pytest tests/ -v
