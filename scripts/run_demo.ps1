<# 
.SYNOPSIS
    Launch the hybrid QKD-PQC secure chat demo.

.DESCRIPTION
    Opens two PowerShell windows: one for the server (Bob) and one for
    the client (Alice). They perform the hybrid handshake and enter
    an encrypted chat.

.PARAMETER Mode
    Handshake mode: hybrid, pqc, qkd, or classical. Default: hybrid.

.PARAMETER EveRate
    Eve's intercept rate (0.0 = no Eve, 1.0 = full intercept). Default: 0.0.

.PARAMETER Noise
    Channel noise probability. Default: 0.0.

.PARAMETER Port
    TCP port. Default: 9000.

.PARAMETER Qubits
    Number of BB84 qubits. Default: 4096.

.EXAMPLE
    .\scripts\run_demo.ps1
    # Normal hybrid handshake, no Eve.

.EXAMPLE
    .\scripts\run_demo.ps1 -EveRate 1.0
    # Eve intercepts all qubits → both sides abort (QBER ~25%).

.EXAMPLE
    .\scripts\run_demo.ps1 -Mode pqc
    # PQC-only mode (no BB84 phase).
#>

param(
    [ValidateSet("hybrid", "pqc", "qkd", "classical")]
    [string]$Mode = "hybrid",

    [ValidateRange(0.0, 1.0)]
    [double]$EveRate = 0.0,

    [ValidateRange(0.0, 1.0)]
    [double]$Noise = 0.0,

    [int]$Port = 9000,

    [int]$Qubits = 4096
)

$ErrorActionPreference = "Stop"
$ProjectRoot = Split-Path -Parent $PSScriptRoot
$VenvPython = Join-Path $ProjectRoot ".venv\Scripts\python.exe"

if (-not (Test-Path $VenvPython)) {
    Write-Error "Virtual environment not found at $VenvPython. Run setup first."
    exit 1
}

Write-Host "Starting Hybrid QKD-PQC Demo" -ForegroundColor Cyan
Write-Host "  Mode     : $Mode"
Write-Host "  Eve Rate : $EveRate"
Write-Host "  Noise    : $Noise"
Write-Host "  Port     : $Port"
Write-Host "  Qubits   : $Qubits"
Write-Host ""

# Start the server in a new PowerShell window
$serverCmd = "& '$VenvPython' -m network.server --mode $Mode --eve-rate $EveRate --noise $Noise --port $Port --qubits $Qubits"
Start-Process powershell -ArgumentList "-NoExit", "-Command", "Set-Location '$ProjectRoot'; Write-Host 'SERVER (Bob)' -ForegroundColor Green; $serverCmd"

# Give the server time to start
Start-Sleep -Seconds 2

# Start the client in a new PowerShell window
$clientCmd = "& '$VenvPython' -m network.client --mode $Mode --port $Port --qubits $Qubits"
Start-Process powershell -ArgumentList "-NoExit", "-Command", "Set-Location '$ProjectRoot'; Write-Host 'CLIENT (Alice)' -ForegroundColor Cyan; $clientCmd"

Write-Host "Server and client windows launched." -ForegroundColor Green
Write-Host "Type messages in either window. Type /quit to disconnect." -ForegroundColor Yellow
