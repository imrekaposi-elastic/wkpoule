# Sync wkpoule-prd deploy token into GitHub Actions secrets.
# Requires: oc (logged in), gh (logged in via `gh auth login`).
#
# Usage:
#   .\scripts\set-github-prd-secrets.ps1
#   .\scripts\set-github-prd-secrets.ps1 -Environment production

param(
    [string]$Environment = "",
    [string]$ApiUrl = "https://api.cloud.kaposi.net:6443"
)

$ErrorActionPreference = "Stop"

if (-not (Get-Command oc -ErrorAction SilentlyContinue)) {
    throw "oc not found on PATH"
}
if (-not (Get-Command gh -ErrorAction SilentlyContinue)) {
    throw "gh not found. Install GitHub CLI and run: gh auth login"
}

gh auth status 2>&1 | Out-Null
if ($LASTEXITCODE -ne 0) {
    throw "Run 'gh auth login' first."
}

$tokenFile = Join-Path $env:TEMP "wkpoule-prd-github-token.txt"
oc extract secret/github-actions-deploy-token -n wkpoule-prd --keys=token --to="$tokenFile" | Out-Null
$token = (Get-Content -Raw $tokenFile).Trim()
Remove-Item -Force $tokenFile

if ([string]::IsNullOrWhiteSpace($token)) {
    throw "Empty token from wkpoule-prd. Apply sa-token-github-deploy.yaml first."
}

$secretArgs = @("secret", "set", "OPENSHIFT_TOKEN_PRD", "--body", $token, "--repo", "imrekaposi-elastic/wkpoule")
if ($Environment) {
    $secretArgs += @("--env", $Environment)
}
& gh @secretArgs

$urlArgs = @("secret", "set", "OPENSHIFT_API_URL_PRD", "--body", $ApiUrl, "--repo", "imrekaposi-elastic/wkpoule")
if ($Environment) {
    $urlArgs += @("--env", $Environment)
}
& gh @urlArgs

Write-Host "Set OPENSHIFT_TOKEN_PRD and OPENSHIFT_API_URL_PRD$(if ($Environment) { " on environment '$Environment'" })."
Write-Host "Re-run Deploy production with confirm=deploy."
