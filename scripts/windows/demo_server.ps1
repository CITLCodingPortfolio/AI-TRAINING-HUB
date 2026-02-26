param([int]$Port = 8787)
$ErrorActionPreference = "Stop"
$Repo = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path
Set-Location $Repo
$py = Join-Path $Repo ".venv\Scripts\python.exe"
if (!(Test-Path $py)) {
  Write-Host "No venv found. Running setup..." -ForegroundColor Yellow
  & (Join-Path $Repo "scripts\windows\setup.ps1")
}
Write-Host "Starting Demo API: http://127.0.0.1:$Port" -ForegroundColor Cyan
& $py -m uvicorn app.demo_api:app --host 127.0.0.1 --port $Port