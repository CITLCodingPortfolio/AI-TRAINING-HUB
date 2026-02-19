$ErrorActionPreference = "Stop"
& "$PSScriptRoot\..\ollama\bootstrap.ps1"
& "$PSScriptRoot\write_runtime_env.ps1"
Write-Host "[bootstrap] done."
