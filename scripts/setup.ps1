param(
  [switch]$Agents,
  [switch]$Rag,
  [string]$Port = "8502"
)
$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $MyInvocation.MyCommand.Path
$repo = Resolve-Path (Join-Path $root "..")
Set-Location $repo
Write-Host "=== AI Training Hub Setup ===" -ForegroundColor Cyan
Write-Host "Repo: $repo"
# 1) Create venv
if (-not (Test-Path ".\.venv")) {
  Write-Host "Creating virtual environment..." -ForegroundColor Cyan
  python -m venv .venv
}
# 2) Activate venv
& "$repo\.venv\Scripts\Activate.ps1"
# 3) Upgrade pip
python -m pip install --upgrade pip
# 4) Install base hub requirements
Write-Host "Installing base Hub requirements..." -ForegroundColor Cyan
pip install -r ".\requirements\requirements-hub.txt"
# 5) Optional: agent frameworks
if ($Agents) {
  Write-Host "Installing agent frameworks (LangGraph / CrewAI / AutoGen)..." -ForegroundColor Cyan
  pip install -r ".\requirements\requirements-agents.txt"
} else {
  Write-Host "Skipping agent frameworks. Re-run with -Agents to install." -ForegroundColor Yellow
}
# 6) Optional: RAG
if ($Rag) {
  Write-Host "Installing RAG stack (Chroma + embeddings + PDF ingestion)..." -ForegroundColor Cyan
  pip install -r ".\requirements\requirements-rag.txt"
} else {
  Write-Host "Skipping RAG stack. Re-run with -Rag to install." -ForegroundColor Yellow
}
Write-Host "✅ Setup complete." -ForegroundColor Green
Write-Host "Starting Hub on port $Port..." -ForegroundColor Green
streamlit run ".\app\hub.py" --server.port $Port
