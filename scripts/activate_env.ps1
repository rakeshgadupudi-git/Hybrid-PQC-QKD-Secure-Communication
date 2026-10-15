# Helper script to activate the hybrid-qkd-pqc virtual environment
# In PowerShell, if script execution is restricted, run:
#   Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectRoot = Split-Path -Parent $ScriptDir
$ActivateScript = Join-Path $ProjectRoot ".venv\Scripts\Activate.ps1"

if (Test-Path $ActivateScript) {
    Write-Host "Activating virtual environment (.venv) for hybrid-qkd-pqc..." -ForegroundColor Cyan
    & $ActivateScript
    Write-Host "Environment activated! Python: $(python --version)" -ForegroundColor Green
    Write-Host "To run the dashboard: streamlit run dashboard/app.py" -ForegroundColor Yellow
} else {
    Write-Error "Virtual environment not found at $ActivateScript. Please ensure .venv exists."
}
