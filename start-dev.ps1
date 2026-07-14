# Local host (no Docker) — Vite UI + API on two ports
# UI:  http://127.0.0.1:5173  (proxies /api → :8000)
# API: http://127.0.0.1:8000
# Usage:  powershell -ExecutionPolicy Bypass -File .\start-dev.ps1

$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot

if (-not (Test-Path .\.venv\Scripts\python.exe)) {
  Write-Host "Creating .venv ..."
  python -m venv .venv
  & .\.venv\Scripts\python.exe -m pip install -r backend\requirements.txt
}

if (-not (Test-Path .\frontend\node_modules)) {
  Push-Location frontend
  npm install
  Pop-Location
}

$api = Start-Process -PassThru -NoNewWindow `
  -FilePath ".\.venv\Scripts\python.exe" `
  -ArgumentList "-m","uvicorn","backend.app.main:app","--reload","--host","127.0.0.1","--port","8000"

Write-Host "API PID $($api.Id) → http://127.0.0.1:8000"
Write-Host "Starting Vite … open http://127.0.0.1:5173"
Write-Host "Close this window / Ctrl+C stops Vite; then stop the API process if needed."

try {
  Push-Location frontend
  npm run dev
} finally {
  Pop-Location
  if (-not $api.HasExited) { Stop-Process -Id $api.Id -Force -ErrorAction SilentlyContinue }
}
