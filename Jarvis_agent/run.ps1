# JARVIS Launcher Script for Windows 11 (PowerShell)
Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host "                JARVIS AI ASSISTANT v3.0.0               " -ForegroundColor Cyan
Write-Host "==========================================================" -ForegroundColor Cyan

$CurrentDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $CurrentDir

# Check if .env exists
if (-not (Test-Path ".env")) {
    Write-Host "[!] .env file not found. Creating from .env.example..." -ForegroundColor Yellow
    Copy-Item ".env.example" ".env"
    Write-Host "[+] Created .env file. Please review your API keys if needed." -ForegroundColor Green
}

# Determine Python / UV path
if (Test-Path ".venv\Scripts\python.exe") {
    $PythonExe = ".venv\Scripts\python.exe"
} elseif (Get-Command uv -ErrorAction SilentlyContinue) {
    Write-Host "[*] Launching via uv runner..." -ForegroundColor Cyan
    & uv run uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
    exit
} else {
    $PythonExe = "python"
}

Write-Host "[*] Starting JARVIS Backend Server on http://127.0.0.1:8000 ..." -ForegroundColor Green
& $PythonExe -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
