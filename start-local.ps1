# Local host (no Docker) — single port http://127.0.0.1:8000
# Prerequisites: Python 3.11+, Node 20+
# Usage:  powershell -ExecutionPolicy Bypass -File .\start-local.ps1

$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot

if (-not (Test-Path .\.venv\Scripts\python.exe)) {
  Write-Host "Creating .venv ..."
  python -m venv .venv
}

$py = ".\.venv\Scripts\python.exe"
Write-Host "Ensuring Python packages ..."
& $py -m pip install --upgrade pip
& $py -m pip install -r backend\requirements.txt

if (-not (Test-Path .\frontend\node_modules)) {
  Write-Host "npm install ..."
  Push-Location frontend
  npm install
  Pop-Location
}

Write-Host "Building frontend ..."
Push-Location frontend
npm run build
Pop-Location

$env:SERVE_FRONTEND = "1"
Write-Host ""
Write-Host "Dashboard: http://127.0.0.1:8000"
Write-Host "API docs:  http://127.0.0.1:8000/docs"
Write-Host "Ctrl+C to stop"
Write-Host ""
& $py -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000
