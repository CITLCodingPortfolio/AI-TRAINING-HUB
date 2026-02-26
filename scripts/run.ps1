param(
  [string]$Port = "8502"
)
$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $MyInvocation.MyCommand.Path
$repo = Resolve-Path (Join-Path $root "..")
Set-Location $repo
if (-not (Test-Path ".\.venv")) {
  Write-Host "Missing .venv. Run scripts\setup.ps1 first." -ForegroundColor Yellow
  exit 1
}
& "$repo\.venv\Scripts\Activate.ps1"
streamlit run ".\app\hub.py" --server.port $Port
