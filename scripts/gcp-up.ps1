[CmdletBinding()]
param(
    [string]$Project,
    [string]$Region = "asia-south1",
    [string]$Repo = "Raxit-AI-Portfolio/mlops-batch-pipeline",
    [string]$DagshubUser = "raxitsoni-ai",
    [switch]$SkipData,
    [switch]$NoTrigger,
    [switch]$Yes
)

$ErrorActionPreference = "Stop"
$RepoRoot = Split-Path -Parent $PSScriptRoot
$TfDir = Join-Path $RepoRoot "infra\gcp"
$SecretId = "dagshub-token"
$script:Token = $null
. (Join-Path $PSScriptRoot "common.ps1")
if (-not $Project) { $Project = Get-LocalSetting "GCP_PROJECT" }
$env:TF_VAR_project_id = $Project

function Get-Token {
    if (-not $script:Token) {
        $s = Read-Host "DagsHub access token" -AsSecureString
        $script:Token = [Runtime.InteropServices.Marshal]::PtrToStringAuto([Runtime.InteropServices.Marshal]::SecureStringToBSTR($s))
    }
    $script:Token
}

Write-Host "== 1. Pre-flight checks"
$null = Get-LocalSetting "GCP_BACKUP_DIR"
foreach ($cmd in "gcloud", "terraform", "gh", "dvc") {
    if (-not (Get-Command $cmd -ErrorAction SilentlyContinue)) { throw "'$cmd' not found on PATH (activate .venv for dvc)." }
}
$activeProject = Get-NativeOutput gcloud @("config", "get-value", "project")
if ($activeProject -ne $Project) { throw "gcloud project is '$activeProject', expected '$Project'. Run: gcloud config set project $Project" }
if (-not ((Get-NativeOutput gcloud @("auth", "application-default", "print-access-token")) -match '^ya29')) {
    throw "ADC missing. Run: gcloud auth application-default login"
}
Invoke-Native gh @("auth", "status")

Push-Location $TfDir
try {
    Write-Host "== 2. terraform init"
    Invoke-Native terraform @("init", "-input=false")

    Write-Host "== 3. Phase 1: secret plumbing"
    $targets = @(
        "-target=google_project_service.secretmanager",
        "-target=google_secret_manager_secret.dagshub_token",
        "-target=google_secret_manager_secret_iam_member.runtime_access"
    )
    Invoke-Native terraform (@("plan", "-input=false", "-out=tfplan1") + $targets)
    Confirm-Step "Apply phase 1 (creates the Secret Manager secret and its IAM)?"
    Invoke-Native terraform @("apply", "-input=false", "tfplan1")

    Write-Host "== 4. DagsHub token in Secret Manager"
    $enabled = gcloud secrets versions list $SecretId --filter="state=enabled" --format="value(name)" --project $Project
    if (-not $enabled) {
        $tmp = Join-Path $env:TEMP "dagshub-token.txt"
        try {
            [IO.File]::WriteAllText($tmp, (Get-Token))
            Invoke-Native gcloud @("secrets", "versions", "add", $SecretId, "--data-file", $tmp, "--project", $Project)
        }
        finally { Remove-Item $tmp -ErrorAction SilentlyContinue }
    }
    else { Write-Host "Secret already has an enabled version, skipping." }

    Write-Host "== 5. Phase 2: remaining resources"
    Invoke-Native terraform @("plan", "-input=false", "-out=tfplan2")
    Confirm-Step "Apply phase 2 (creates bucket, registry, service accounts, WIF, Cloud Run)?"
    Invoke-Native terraform @("apply", "-input=false", "tfplan2")
    Backup-State

    $out = terraform output -json | ConvertFrom-Json
}
finally { Pop-Location }

Write-Host "== 6. GitHub repo variables and secret"
$vars = @{
    WIF_PROVIDER = $out.wif_provider.value
    DEPLOYER_SA  = $out.deployer_sa_email.value
    GCP_PROJECT  = $Project
    GCP_REGION   = $Region
    DAGSHUB_USER = $DagshubUser
}
foreach ($k in $vars.Keys) { Invoke-Native gh @("variable", "set", $k, "--body", $vars[$k], "--repo", $Repo) }
if (-not (gh secret list --repo $Repo | Select-String "^DAGSHUB_TOKEN")) {
    Invoke-Native gh @("secret", "set", "DAGSHUB_TOKEN", "--body", (Get-Token), "--repo", $Repo)
}

Write-Host "== 7. DVC remote 'gcs'"
Push-Location $RepoRoot
try {
    $dvcUrl = $out.dvc_remote_url.value
    if (-not (dvc remote list | Select-String ("^gcs\s+" + [regex]::Escape($dvcUrl)))) {
        Invoke-Native dvc @("remote", "modify", "--local", "gcs", "url", $dvcUrl)
        Write-Host "DVC remote 'gcs' set in .dvc/config.local (not committed). CI sets it from the GCP_PROJECT variable."
    }
    if (-not $SkipData) { Invoke-Native dvc @("push", "-r", "gcs") }

    Write-Host "== 8. Prometheus config for the new Cloud Run URL"
    $appHost = ([uri]$out.app_url.value).Host
    $base = [IO.File]::ReadAllText((Join-Path $RepoRoot "monitoring\prometheus.yml"))
    $prodJob = @"

  - job_name: app-prod
    scheme: https
    metrics_path: /metrics
    scrape_interval: 60s
    scrape_timeout: 30s
    static_configs:
      - targets: ["${appHost}:443"]
        labels: {env: prod}
"@
    [IO.File]::WriteAllText((Join-Path $RepoRoot "monitoring\prometheus.prod.yml"), $base.TrimEnd() + "`n" + $prodJob)

    Write-Host "== 9. Enable workflows"
    foreach ($wf in "train.yml", "register-deploy.yml") { Invoke-Native gh @("workflow", "enable", $wf, "--repo", $Repo) }
    if (-not $NoTrigger) { Invoke-Native gh @("workflow", "run", "train.yml", "--repo", $Repo, "--ref", "main") }
}
finally { Pop-Location }

Write-Host ""
Write-Host "Done."
Write-Host "  Cloud Run URL : $($out.app_url.value)"
Write-Host "  Registry      : $($out.image_repo.value)"
Write-Host "  Watch pipeline: gh run list --repo $Repo"
Write-Host "  Prometheus    : `$env:PROM_CONFIG='../monitoring/prometheus.prod.yml'; docker compose -f infra/docker-compose.yml up prometheus grafana"
Write-Host "  The Cloud Run service shows the placeholder page until register-deploy finishes."
