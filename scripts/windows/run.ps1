param(
  [int]$Port = 8502,
  [switch]$StartOllama
)
$ErrorActionPreference = "Stop"
$Repo = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path
Set-Location $Repo
$py = Join-Path $Repo ".venv\Scripts\python.exe"
if (!(Test-Path $py)) { throw "Missing venv. Run: .\scripts\windows\setup.ps1" }
# Optional: start Ollama if installed (does not install)
if ($StartOllama) {
  $ollama = @(
    "$env:LOCALAPPDATA\Programs\Ollama\ollama.exe",
    "$env:ProgramFiles\Ollama\ollama.exe",
    "$env:ProgramFiles(x86)\Ollama\ollama.exe"
  ) | Where-Object { Test-Path $_ } | Select-Object -First 1
  if ($ollama) {
    $env:Path = (Split-Path $ollama -Parent) + ";" + $env:Path
    Start-Process -FilePath $ollama -ArgumentList "serve" -WindowStyle Hidden -ErrorAction SilentlyContinue | Out-Null
    Start-Sleep 1
    Write-Host "Ollama started (or already running): $ollama" -ForegroundColor Green
  } else {
    Write-Warning "Ollama not found. Install Ollama first."
  }
}
Write-Host "Launching Hub: $Repo\app\hub.py (port $Port)..." -ForegroundColor Cyan
& $py -m streamlit run (Join-Path $Repo "app\hub.py") --server.port $Port