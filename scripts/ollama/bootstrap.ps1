Param(
  [string]$RepoRoot = (Resolve-Path "$PSScriptRoot\..\..").Path
)

$ErrorActionPreference = "Stop"

function Ensure-Ollama {
  if (Get-Command ollama -ErrorAction SilentlyContinue) { return }

  Write-Host "[ollama] not found -> installing via winget..."
  # Official Winget package id
  winget install -e --id Ollama.Ollama
}

function Ensure-OllamaRunning {
  try {
    ollama list | Out-Null
    return
  } catch {}

  Write-Host "[ollama] starting daemon..."
  Start-Process -WindowStyle Hidden -FilePath "ollama" -ArgumentList "serve"
  Start-Sleep -Seconds 2
  ollama list | Out-Null
}

function Scan-Modelfiles {
  Get-ChildItem -Path $RepoRoot -Recurse -File -Filter "Modelfile" |
    Where-Object { $_.FullName -notmatch "\\.git\\" -and $_.FullName -notmatch "\\.venv\\" } |
    ForEach-Object {
      $mf = $_.FullName
      $dir = Split-Path $mf -Parent
      $name = Split-Path $dir -Leaf

      $override = (Select-String -Path $mf -Pattern '^\s*#\s*NAME:\s*' -ErrorAction SilentlyContinue | Select-Object -First 1).Line
      if ($override) { $name = ($override -replace '^\s*#\s*NAME:\s*','').Trim() }

      $fromLine = (Select-String -Path $mf -Pattern '^\s*FROM\s+' -ErrorAction SilentlyContinue | Select-Object -First 1).Line
      $from = ""
      if ($fromLine) { $from = ($fromLine -split "\s+")[1] }

      [pscustomobject]@{ Name=$name; Modelfile=$mf; From=$from }
    }
}

Ensure-Ollama
Ensure-OllamaRunning

Write-Host "[ollama] scanning for Modelfiles..."
$rows = @(Scan-Modelfiles)

if ($rows.Count -eq 0) {
  Write-Host "[ollama] No Modelfiles found. Nothing to graft."
  exit 0
}

Write-Host "[ollama] pulling base models referenced by FROM..."
foreach ($r in $rows) {
  if ($r.From) {
    Write-Host "  -> ollama pull $($r.From)"
    ollama pull $r.From
  }
}

Write-Host "[ollama] creating custom models from Modelfiles..."
foreach ($r in $rows) {
  Write-Host "  -> ollama create $($r.Name) -f $($r.Modelfile)"
  ollama create $r.Name -f $r.Modelfile
}

Write-Host "[ollama] done. Installed models:"
ollama list
