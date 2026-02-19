param(
  [string]$RepoUrl = "",
  [string]$Branch = "main",
  [string]$Message = "Update AI Training Hub"
)
$ErrorActionPreference = "Stop"
Set-Location -Path $PSScriptRoot
if (-not (Get-Command git -ErrorAction SilentlyContinue)) {
  throw "git not found. Install Git for Windows and reopen PowerShell."
}
if (-not (Test-Path ".git")) {
  git init
}
$hasOrigin = (git remote) -contains "origin"
if (-not $hasOrigin) {
  if ([string]::IsNullOrWhiteSpace($RepoUrl)) {
    throw "No 'origin' remote set. Re-run with -RepoUrl <YOUR_GITHUB_REPO_URL>."
  }
  git remote add origin $RepoUrl
} elseif (-not [string]::IsNullOrWhiteSpace($RepoUrl)) {
  git remote set-url origin $RepoUrl
}
git checkout -B $Branch
git add -A
try {
  git commit -m $Message
} catch {
  Write-Host "No changes to commit (continuing)..."
}
git push -u origin $Branch
Write-Host "✅ Pushed to GitHub branch '$Branch'"
