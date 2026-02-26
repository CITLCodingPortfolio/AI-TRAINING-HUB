param(
  [Parameter(Mandatory=$true)][string]$Bot,
  [string]$Input,
  [string]$InputFile,
  [string[]]$File = @(),
  [string]$Api = "http://127.0.0.1:8787",
  [switch]$NoServer
)
$ErrorActionPreference = "Stop"
$Repo = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path
Set-Location $Repo
$py = Join-Path $Repo ".venv\Scripts\python.exe"
if (!(Test-Path $py)) { throw "Missing venv. Run: .\scripts\windows\setup.ps1" }
$args = @("scripts\demo\run_bot.py","--bot",$Bot,"--api",$Api)
if ($NoServer) { $args += "--no-server" }
if ($Input) { $args += @("--input",$Input) }
if ($InputFile) { $args += @("--input-file",$InputFile) }
foreach ($f in $File) { $args += @("--file",$f) }
& $py @args