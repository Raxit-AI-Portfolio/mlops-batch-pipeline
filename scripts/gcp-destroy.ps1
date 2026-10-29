[CmdletBinding()]
param(
    [string]$Project,
    [string]$Repo = "Raxit-AI-Portfolio/mlops-batch-pipeline"
)

$ErrorActionPreference = "Stop"
$RepoRoot = Split-Path -Parent $PSScriptRoot
$TfDir = Join-Path $RepoRoot "infra\gcp"
. (Join-Path $PSScriptRoot "common.ps1")
if (-not $Project) { $Project = Get-LocalSetting "GCP_PROJECT" }
$env:TF_VAR_project_id = $Project

Write-Host "== 1. Pre-flight checks"
$null = Get-LocalSetting "GCP_BACKUP_DIR"
foreach ($cmd in "gcloud", "terraform") {
    if (-not (Get-Command $cmd -ErrorAction SilentlyContinue)) { throw "'$cmd' not found on PATH." }
}
$activeProject = Get-NativeOutput gcloud @("config", "get-value", "project")
if ($activeProject -ne $Project) { throw "gcloud project is '$activeProject', expected '$Project'." }
if (-not ((Get-NativeOutput gcloud @("auth", "application-default", "print-access-token")) -match '^ya29')) {
    throw "ADC missing. Run: gcloud auth application-default login"
}

Push-Location $TfDir
try {
    Invoke-Native terraform @("init", "-input=false")
    $resources = terraform state list
    if (-not $resources) { Write-Host "Terraform state is empty. Nothing to destroy."; return }
    Write-Host "Resources in state:"; $resources | ForEach-Object { Write-Host "  $_" }

    Write-Host "== 2. Back up state"
    Backup-State

    Write-Host "== 3. Allow bucket deletion (state-only change, no GCP resource touched)"
    Invoke-Native terraform @("plan", "-input=false", "-var", "force_destroy=true", "-target=google_storage_bucket.dvc", "-out=tfdestroy1")
    Invoke-Native terraform @("apply", "-input=false", "tfdestroy1")

    Write-Host "== 4. Destroy plan"
    Invoke-Native terraform @("plan", "-destroy", "-input=false", "-var", "force_destroy=true", "-out=tfdestroy")
    Write-Host ""
    Write-Host "This DELETES the resources above, including the DVC bucket and every object version in it."
    if ((Read-Host "Type the project id '$Project' to continue") -ne $Project) { throw "Aborted: project id did not match." }
    Invoke-Native terraform @("apply", "-input=false", "tfdestroy")

    Write-Host "== 5. Verify"
    $left = terraform state list
    if ($left) { throw "State still lists: $($left -join ', ')" }
}
finally { Pop-Location }

Write-Host "Remaining resources (read-only check):"
gcloud run services list --region asia-south1 --project $Project
gcloud storage buckets list --project $Project
gcloud artifacts repositories list --project $Project
gcloud secrets list --project $Project

Write-Host "== 6. Clean up local and GitHub leftovers"
Remove-Item (Join-Path $RepoRoot "monitoring\prometheus.prod.yml") -ErrorAction SilentlyContinue
if (Get-Command gh -ErrorAction SilentlyContinue) {
    foreach ($v in "WIF_PROVIDER", "DEPLOYER_SA") { $null = Get-NativeOutput gh @("variable", "delete", $v, "--repo", $Repo) }
}

Write-Host ""
Write-Host "Done. GCP resources destroyed, state empty. The GCP project itself still exists (no cost)."
Write-Host "Rebuild with: .\scripts\gcp-up.ps1"
