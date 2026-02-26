<#
.SYNOPSIS
    Kill and restart the Ollama server. Run this whenever Ollama is hung,
    unresponsive, or you want a clean state before launching the sandbox.

.PARAMETER Action
    start   — start Ollama (default)
    stop    — kill Ollama only
    restart — kill then start (default when Ollama is already running)

.EXAMPLE
    .\scripts\windows\manage_ollama.ps1
    .\scripts\windows\manage_ollama.ps1 -Action stop
    .\scripts\windows\manage_ollama.ps1 -Action restart
#>
param(
    [ValidateSet("start","stop","restart")]
    [string]$Action = "start"
)

function Stop-Ollama {
    Write-Host "  Stopping Ollama processes ..." -ForegroundColor Yellow
    foreach ($name in @("ollama.exe","ollama_llama_server.exe")) {
        $procs = Get-Process -Name ($name -replace '\.exe','') -ErrorAction SilentlyContinue
        if ($procs) {
            $procs | Stop-Process -Force -ErrorAction SilentlyContinue
            Write-Host "    Killed: $name" -ForegroundColor DarkGray
        }
    }
    Start-Sleep -Seconds 1
    Write-Host "  Ollama stopped." -ForegroundColor Green
}

function Start-Ollama {
    Write-Host "  Starting Ollama ..." -ForegroundColor Cyan
    Start-Process -FilePath "ollama" -ArgumentList "serve" `
        -WindowStyle Hidden -ErrorAction Stop
    Write-Host "  Waiting for Ollama to be ready" -ForegroundColor DarkGray -NoNewline
    $ready = $false
    for ($i = 0; $i -lt 15; $i++) {
        Start-Sleep -Seconds 1
        Write-Host "." -NoNewline
        try {
            $r = Invoke-WebRequest -Uri "http://localhost:11434/api/tags" `
                -UseBasicParsing -TimeoutSec 2 -ErrorAction Stop
            if ($r.StatusCode -eq 200) { $ready = $true; break }
        } catch { }
    }
    Write-Host ""
    if ($ready) {
        Write-Host "  Ollama is ready." -ForegroundColor Green
    } else {
        Write-Host "  WARNING: Ollama did not respond in time. Check 'ollama serve' manually." -ForegroundColor Red
    }
}

Write-Host ""
Write-Host "  AI Training Hub — Ollama Manager" -ForegroundColor Cyan
Write-Host ""

$running = $false
try {
    $r = Invoke-WebRequest -Uri "http://localhost:11434/api/tags" `
        -UseBasicParsing -TimeoutSec 2 -ErrorAction Stop
    $running = ($r.StatusCode -eq 200)
} catch { }

switch ($Action) {
    "stop"    { Stop-Ollama }
    "start"   {
        if ($running) {
            Write-Host "  Ollama already running." -ForegroundColor Green
        } else {
            Start-Ollama
        }
    }
    "restart" {
        Stop-Ollama
        Start-Ollama
    }
    default {
        # Smart default: restart if running (might be hung), start if not
        if ($running) {
            Write-Host "  Ollama detected — restarting for clean state ..." -ForegroundColor Yellow
            Stop-Ollama
            Start-Ollama
        } else {
            Start-Ollama
        }
    }
}
Write-Host ""
