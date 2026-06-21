# Deploy src/web to the gh-pages branch (GitHub Pages).
# Requires: git, push access to origin.
# Usage (from repo root): .\scripts\deploy-gh-pages.ps1

$ErrorActionPreference = "Stop"
$repoRoot = Split-Path -Parent $PSScriptRoot
Set-Location $repoRoot

if (-not (Test-Path "src/web/index.html")) {
    throw "Expected src/web/index.html — run this script from the repository root."
}

Write-Host "Pushing src/web to origin/gh-pages via git subtree..."
git subtree push --prefix src/web origin gh-pages

Write-Host ""
Write-Host "Done. Site URL (after GitHub Pages is enabled):"
Write-Host "  https://mark05e.github.io/bankstatement-liteparse/"
