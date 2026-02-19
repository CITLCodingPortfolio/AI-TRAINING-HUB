param()
$ErrorActionPreference = "Stop"
$Repo = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path
Set-Location $Repo
Write-Host "== AI-Training-Hub Setup (Windows) ==" -ForegroundColor Cyan
Write-Host "Repo: $Repo" -ForegroundColor DarkGray
$py = Join-Path $Repo ".venv\Scripts\python.exe"
if (!(Test-Path $py)) {
  Write-Host "Creating venv (.venv)..." -ForegroundColor Yellow
  python -m venv .venv
}
& $py -m pip install -U pip | Out-Null
function Test-Internet {
  try { (Invoke-WebRequest "https://pypi.org" -UseBasicParsing -TimeoutSec 4).StatusCode -ge 200 } catch { $false }
}
$online = Test-Internet
Write-Host ("Internet: " + ($(if($online){"OK"}else{"OFFLINE"}))) -ForegroundColor DarkGray
# Preferred install order (prevents churn):
# 1) requirements-lock.txt (if present)
# 2) then demo/transcribe/rag extras (if present)
$reqOrder = @(
  "requirements\requirements-lock.txt",
  "requirements\requirements.txt",
  "requirements.txt",
  "requirements\requirements-demo.txt",
  "requirements\requirements-transcribe.txt",
  "requirements\requirements-rag.txt"
)
$reqFiles = @()
foreach ($r in $reqOrder) {
  $p = Join-Path $Repo $r
  if (Test-Path $p) { $reqFiles += $p }
}
$reqFiles = $reqFiles | Select-Object -Unique
if ($online -and $reqFiles.Count -gt 0) {
  foreach ($r in $reqFiles) {
    Write-Host "Installing: $r" -ForegroundColor Yellow
    & $py -m pip install -r $r
  }
} else {
  Write-Warning "Skipping pip install (offline or no requirements files found)."
}
Write-Host "Setup complete." -ForegroundColor Green
Write-Host "Next:" -ForegroundColor White
Write-Host "  1) Start demo API:  .\scripts\windows\demo_server.ps1" -ForegroundColor White
Write-Host "  2) Start Hub GUI:   .\scripts\windows\run.ps1 -Port 8502" -ForegroundColor White