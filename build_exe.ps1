<#
.SYNOPSIS
    Build all AI Training Hub EXEs using PyInstaller.
    Outputs EXEs directly into the repo root — double-click to run.

    EXEs produced:
      "Launch AI Training Hub.exe"  — opens full Streamlit GUI in browser
      sandbox.exe                   — IRC-style colored bot chat CLI

.EXAMPLE
    .\build_exe.ps1
#>

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$RepoRoot = $PSScriptRoot
Set-Location $RepoRoot

$VenvPy  = Join-Path $RepoRoot ".venv\Scripts\python.exe"
$VenvPip = Join-Path $RepoRoot ".venv\Scripts\pip.exe"

if (-not (Test-Path $VenvPy)) {
    Write-Host ""
    Write-Host "  ERROR: venv not found. Run .\scripts\windows\setup.ps1 first." -ForegroundColor Red
    Write-Host ""
    exit 1
}

# ── Step 1: Ensure PyInstaller ────────────────────────────────────────────────
Write-Host ""
Write-Host "  [1/3] Checking PyInstaller..." -ForegroundColor Cyan
$check = & $VenvPy -m pip show pyinstaller 2>&1
if ($check -notmatch "Name: pyinstaller") {
    Write-Host "        Installing PyInstaller..." -ForegroundColor DarkGray
    & $VenvPip install --quiet pyinstaller
    if ($LASTEXITCODE -ne 0) { Write-Host "  ERROR: pip install pyinstaller failed." -ForegroundColor Red; exit 1 }
}
Write-Host "        PyInstaller ready." -ForegroundColor Green

# ── Step 2: Build "Launch AI Training Hub.exe" ───────────────────────────────
Write-Host ""
Write-Host "  [2/3] Building 'Launch AI Training Hub.exe'..." -ForegroundColor Cyan
& $VenvPy -m PyInstaller --clean --noconfirm --distpath . hub_launcher.spec
if ($LASTEXITCODE -ne 0) { Write-Host "  ERROR: hub_launcher build failed." -ForegroundColor Red; exit 1 }
Write-Host "        'Launch AI Training Hub.exe' built." -ForegroundColor Green

# ── Step 3: Build sandbox.exe ─────────────────────────────────────────────────
Write-Host ""
Write-Host "  [3/3] Building sandbox.exe..." -ForegroundColor Cyan
& $VenvPy -m PyInstaller --clean --noconfirm --distpath . sandbox.spec
if ($LASTEXITCODE -ne 0) { Write-Host "  ERROR: sandbox.exe build failed." -ForegroundColor Red; exit 1 }
Write-Host "        sandbox.exe built." -ForegroundColor Green

# ── Done ──────────────────────────────────────────────────────────────────────
Write-Host ""
Write-Host "  ════════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host "   BUILD COMPLETE — EXEs are in the repo root:" -ForegroundColor Green
Write-Host "  ════════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host ""

Get-ChildItem $RepoRoot -Filter "*.exe" | ForEach-Object {
    $size = [math]::Round($_.Length / 1MB, 1)
    Write-Host "     $($_.Name)   ($size MB)" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "  ── How to use ────────────────────────────────────────────" -ForegroundColor DarkGray
Write-Host ""
Write-Host "   Double-click:  'Launch AI Training Hub.exe'" -ForegroundColor White
Write-Host "   → Starts the full GUI (all tabs) in your browser" -ForegroundColor DarkGray
Write-Host "   → Tabs: Environment · Install · Ollama · Bot Builder · Chat …" -ForegroundColor DarkGray
Write-Host "   → Build Ollama models from the Ollama tab (no extra tool needed)" -ForegroundColor DarkGray
Write-Host ""
Write-Host "   Double-click:  sandbox.exe" -ForegroundColor White
Write-Host "   → Opens IRC-style colored chat for any registered bot" -ForegroundColor DarkGray
Write-Host "   → sandbox.exe --bot ollama_bot" -ForegroundColor DarkGray
Write-Host "   → sandbox.exe --bot student_bot" -ForegroundColor DarkGray
Write-Host ""
Write-Host "  NOTE: Both EXEs run without admin rights." -ForegroundColor DarkGray
Write-Host ""
