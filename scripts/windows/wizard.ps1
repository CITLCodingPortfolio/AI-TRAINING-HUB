param(
  [int]$HubPort = 8502,
  [int]$ApiPort = 8787
)
$ErrorActionPreference = "Stop"
$Repo = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path
Set-Location $Repo
function Test-Internet {
  try { (Invoke-WebRequest "https://pypi.org" -UseBasicParsing -TimeoutSec 4).StatusCode -ge 200 } catch { $false }
}
function Test-PortFree([int]$p) {
  try {
    $listener = [System.Net.Sockets.TcpListener]::new([System.Net.IPAddress]::Loopback, $p)
    $listener.Start(); $listener.Stop()
    return $true
  } catch { return $false }
}
function Next-FreePort([int]$start) {
  $p = $start
  while (-not (Test-PortFree $p)) { $p++ }
  return $p
}
Write-Host "== AI TRAINING HUB (Windows Wizard) ==" -ForegroundColor Cyan
Write-Host ("Repo: " + $Repo) -ForegroundColor DarkGray
# venv
$py = Join-Path $Repo ".venv\Scripts\python.exe"
if (!(Test-Path -LiteralPath $py)) {
  Write-Host "Creating venv (.venv)..." -ForegroundColor Yellow
  python -m venv .venv
}
& $py -m pip install -U pip | Out-Null
# requirements selection
$req = @(
  (Join-Path $Repo "requirements\requirements.txt"),
  (Join-Path $Repo "requirements.txt"),
  (Join-Path $Repo "requirements\base.txt")
) | Where-Object { Test-Path $_ } | Select-Object -First 1
$online = Test-Internet
if ($req) {
  if (Test-Path (Join-Path $Repo "wheelhouse")) {
    Write-Host "Installing from OFFLINE wheelhouse\ ..." -ForegroundColor Yellow
    & $py -m pip install --no-index --find-links (Join-Path $Repo "wheelhouse") -r $req
  } elseif ($online) {
    Write-Host "Installing deps (pip)..." -ForegroundColor Yellow
    & $py -m pip install -r $req
  } else {
    Write-Warning "Offline and no wheelhouse\. Skipping pip install."
  }
} else {
  Write-Warning "No requirements file found. Skipping pip install."
}
# ---- start API (optional) ----
if (Test-Path (Join-Path $Repo "bots\api_server.py")) {
  $p = Next-FreePort $ApiPort
  $runtimeDir = Join-Path $Repo "data\runtime"
  New-Item -ItemType Directory -Force -Path $runtimeDir | Out-Null
  Set-Content -Encoding ASCII -Path (Join-Path $runtimeDir "api_port.txt") -Value "$p"
  Write-Host "Starting API on http://127.0.0.1:$p (new window)..." -ForegroundColor Cyan
  Start-Process -FilePath $py -ArgumentList @("-m","bots.api_server","--host","127.0.0.1","--port",$p) -WindowStyle Minimized | Out-Null
} else {
  Write-Warning "bots/api_server.py not found. API not started."
}
# ---- start Hub ----
$hp = Next-FreePort $HubPort
Write-Host "Launching Hub on http://localhost:$hp" -ForegroundColor Green
& $py -m streamlit run (Join-Path $Repo "app\hub.py") --server.port $hp