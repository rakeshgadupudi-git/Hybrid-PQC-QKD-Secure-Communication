<# 
.SYNOPSIS
    Launch the Hybrid QKD-PQC React UI and FastAPI Event Server.

.DESCRIPTION
    Activates the virtual environment, starts the FastAPI backend server on
    port 8000, starts the Vite React dev server on port 5173, and opens
    the web browser to http://localhost:5173.
#>

$ErrorActionPreference = "Stop"
$ProjectRoot = Split-Path -Parent $PSScriptRoot
$VenvPython = Join-Path $ProjectRoot ".venv\Scripts\python.exe"
$UiDir = Join-Path $ProjectRoot "ui"

if (-not (Test-Path $VenvPython)) {
    Write-Error "Virtual environment not found at $VenvPython. Run python -m venv .venv first."
    exit 1
}

Write-Host "=====================================================" -ForegroundColor Cyan
Write-Host " Starting Hybrid QKD-PQC Web Dashboard" -ForegroundColor Cyan
Write-Host "=====================================================" -ForegroundColor Cyan
Write-Host "  Backend API : http://127.0.0.1:8000"
Write-Host "  Frontend UI : http://localhost:5173"
Write-Host ""

# 1. Start FastAPI Backend in a separate window
$backendCmd = "& '$VenvPython' -m uvicorn api.main:app --host 127.0.0.1 --port 8000 --reload"
Write-Host "Launching FastAPI backend..." -ForegroundColor Green
Start-Process powershell -ArgumentList "-NoExit", "-Command", "Set-Location '$ProjectRoot'; Write-Host '--- HYBRID QKD-PQC FASTAPI EVENT BACKEND (Port 8000) ---' -ForegroundColor Green; $backendCmd"

# 2. Wait a moment for the backend socket
Start-Sleep -Seconds 2

# 3. Start React Vite Frontend in a separate window
Write-Host "Launching Vite dev server..." -ForegroundColor Cyan
$frontendCmd = "npm run dev"
Start-Process powershell -ArgumentList "-NoExit", "-Command", "Set-Location '$UiDir'; Write-Host '--- HYBRID QKD-PQC VITE DEV SERVER (Port 5173) ---' -ForegroundColor Cyan; $frontendCmd"

# 4. Wait for Vite to bind and open browser
Write-Host "Waiting for dev servers to stabilize..." -ForegroundColor Yellow
Start-Sleep -Seconds 3

Write-Host "Opening web browser at http://localhost:5173..." -ForegroundColor Green
Start-Process "http://localhost:5173"

Write-Host ""
Write-Host "All services started successfully!" -ForegroundColor Green
Write-Host "Press Ctrl+C in the respective PowerShell windows when ready to stop." -ForegroundColor Gray
