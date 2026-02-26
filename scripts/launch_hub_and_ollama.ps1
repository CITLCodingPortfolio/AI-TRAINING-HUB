# scripts/launch_hub_and_ollama.ps1
# PowerShell 5.1-safe launcher: starts Ollama (if installed) + launches Streamlit Hub.
# No admin required. No placeholders.
$ErrorActionPreference = "Stop"
Write-Host "=== AI TRAINING HUB: Launch (Ollama + Hub) ==="
# Repo root = parent of /scripts
$repoRoot = Split-Path -Parent $PSScriptRoot
Set-Location $repoRoot
Write-Host ("Repo: " + (Get-Location).Path)
# --- Validate venv + hub.py ---
$py = Join-Path $repoRoot ".venv\Scripts\python.exe"
$hubPy = Join-Path $repoRoot "app\hub.py"
if (!(Test-Path $py)) {
  Write-Host "ERROR: Python venv not found at: $py"
  Write-Host "Run: .\scripts\setup.ps1"
  exit 1
}
if (!(Test-Path $hubPy)) {
  Write-Host "ERROR: hub.py not found at: $hubPy"
  exit 1
}
# --- Ollama: detect + start if possible ---
$ollamaExe = Join-Path $env:LOCALAPPDATA "Programs\Ollama\ollama.exe"
$ollamaApi = "http://127.0.0.1:11434/api/version"
function Test-OllamaApi {
  try {
    $r = Invoke-RestMethod -Uri $ollamaApi -Method GET -TimeoutSec 2
    return $true
  } catch {
    return $false
  }
}
if (Test-OllamaApi) {
  Write-Host "Ollama already running at 127.0.0.1:11434"
}
elseif (Test-Path $ollamaExe) {
  Write-Host "Ollama found: $ollamaExe"
  Write-Host "Starting Ollama server (separate window)..."
  Start-Process -FilePath $ollamaExe -ArgumentList "serve" -WindowStyle Minimized
  # Wait up to ~12 seconds for API to respond
  $ok = $false
  for ($i=1; $i -le 12; $i++) {
    Start-Sleep -Milliseconds 1000
    if (Test-OllamaApi) { $ok = $true; break }
  }
  if ($ok) {
    Write-Host "Ollama is up: $ollamaApi"
  } else {
    Write-Host "WARNING: Ollama did not respond yet. Hub will still start."
    Write-Host "If LLM features fail, open a terminal and run:"
    Write-Host "  `"$ollamaExe`" serve"
  }
}
else {
  Write-Host "WARNING: Ollama not found at: $ollamaExe"
  Write-Host "Hub will start, but LLM features will not work until Ollama is installed."
}
# --- Launch Hub (Streamlit) ---
# Use venv python explicitly (reliable on PS 5.1)
Write-Host "Launching Hub on port 8502..."
& $py -m streamlit run $hubPy --server.port 8502
