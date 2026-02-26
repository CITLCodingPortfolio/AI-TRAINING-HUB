<#
.SYNOPSIS
    Launch the Ollama Bot CLI Sandbox (IRC-style colored chat).

.DESCRIPTION
    Activates the venv and starts the interactive sandbox REPL.
    Each bot gets its own color. Students can swap bots with /bot <id>.

.PARAMETER Bot
    Bot ID from registry. Sets bot name + color automatically.
    Example: -Bot student_bot

.PARAMETER Model
    Override Ollama model tag (default: hub-assistant).
    Example: -Model llama3.2

.PARAMETER Color
    Force a specific bot response color (#RRGGBB).
    Example: -Color "#FF6B6B"

.PARAMETER Host
    Ollama base URL. Default: http://localhost:11434
    Example: -Host "http://192.168.1.10:11434"

.PARAMETER NoStream
    Disable token streaming (show full reply after completion).

.EXAMPLE
    # Default hub-assistant bot
    .\scripts\windows\run_ollama_sandbox.ps1

.EXAMPLE
    # Student bot with registry color
    .\scripts\windows\run_ollama_sandbox.ps1 -Bot student_bot

.EXAMPLE
    # Custom color override
    .\scripts\windows\run_ollama_sandbox.ps1 -Bot student_bot -Color "#FF6B6B"

.EXAMPLE
    # Use a raw llama3.2 model, custom color
    .\scripts\windows\run_ollama_sandbox.ps1 -Model llama3.2 -Color "#A78BFA"
#>

param(
    [string]$Bot      = "",
    [string]$Model    = "",
    [string]$Color    = "",
    [string]$Host     = "",
    [switch]$NoStream
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

# ── Locate repo root (script is in scripts/windows/) ──────────────────────────
$RepoRoot = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)
Set-Location $RepoRoot

# ── Activate venv ──────────────────────────────────────────────────────────────
$VenvPy = Join-Path $RepoRoot ".venv\Scripts\python.exe"
if (-not (Test-Path $VenvPy)) {
    Write-Host "ERROR: venv not found at .venv\  Run .\scripts\windows\setup.ps1 first." -ForegroundColor Red
    exit 1
}

# ── Build argument list ────────────────────────────────────────────────────────
$PyArgs = @("-m", "bots.ollama_sandbox")
if ($Bot)      { $PyArgs += "--bot",   $Bot   }
if ($Model)    { $PyArgs += "--model", $Model }
if ($Color)    { $PyArgs += "--color", $Color }
if ($Host)     { $PyArgs += "--host",  $Host  }
if ($NoStream) { $PyArgs += "--no-stream"      }

Write-Host ""
Write-Host "  AI Training Hub — Ollama Bot Sandbox" -ForegroundColor Cyan
Write-Host "  Launching: python $($PyArgs -join ' ')" -ForegroundColor DarkGray
Write-Host ""

& $VenvPy @PyArgs
