Param(
  [string]$RepoRoot = (Resolve-Path "$PSScriptRoot\..\..").Path
)

$ErrorActionPreference = "Stop"

# Load runtime.env (bash-style exports) into PowerShell env
$envFile = Join-Path $RepoRoot "config\runtime.env"
if (Test-Path $envFile) {
  Get-Content $envFile | ForEach-Object {
    if ($_ -match '^\s*export\s+([A-Za-z_][A-Za-z0-9_]*)="?(.*?)"?\s*$') {
      $name = $Matches[1]
      $val  = $Matches[2]
      $env:$name = $val
    }
  }
}

Set-Location $RepoRoot

# venv activation if present (PowerShell venv)
$venvPs1 = Join-Path $RepoRoot ".venv\Scripts\Activate.ps1"
if (Test-Path $venvPs1) { . $venvPs1 }

$ep = $env:CITL_STREAMLIT_ENTRYPOINT
if (-not $ep) {
  foreach ($cand in @("streamlit_app.py","app.py","main.py","ui.py")) {
    if (Test-Path (Join-Path $RepoRoot $cand)) { $ep = $cand; break }
  }
}
if (-not $ep) { throw "No Streamlit entrypoint found. Set CITL_STREAMLIT_ENTRYPOINT in config/runtime.env" }

python -m streamlit run $ep
