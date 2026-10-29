[CmdletBinding()]
param(
    [switch]$SkipSeed,
    [switch]$NoBuild
)

$ErrorActionPreference = "Stop"
$RepoRoot = Split-Path -Parent $PSScriptRoot
$Compose = Join-Path $RepoRoot "infra\docker-compose.yml"
$Py = Join-Path $RepoRoot ".venv\Scripts\python.exe"
. (Join-Path $PSScriptRoot "common.ps1")

function Wait-Http([string]$Url, [int]$TimeoutSec) {
    $deadline = (Get-Date).AddSeconds($TimeoutSec)
    while ((Get-Date) -lt $deadline) {
        try { Invoke-WebRequest -Uri $Url -UseBasicParsing -TimeoutSec 5 | Out-Null; return }
        catch { Start-Sleep -Seconds 3 }
    }
    throw "Timed out waiting for $Url"
}

function Test-ModelRegistered {
    try { Invoke-RestMethod "http://localhost:5000/api/2.0/mlflow/registered-models/get?name=IrisClassifier" | Out-Null; $true }
    catch { $false }
}

Write-Host "== 1. Pre-flight checks"
$null = Get-NativeOutput docker @("info")
if ($script:LastNativeExit -ne 0) { throw "Docker is not running." }
if (-not (Test-Path $Py)) { throw "Missing $Py. Create .venv and run: pip install -r requirements.txt -r requirements-dev.txt; pip install -e ." }

Write-Host "== 2. Start storage, MLflow and image registry"
Invoke-Native docker @("compose", "-f", $Compose, "up", "-d", "fake-gcs", "mlflow", "registry")
Wait-Http "http://localhost:5000/health" 90

if (-not $SkipSeed) {
    Write-Host "== 3. Seed model registry (train, evaluate gate, register)"
    if (Test-ModelRegistered) { Write-Host "IrisClassifier already registered, skipping." }
    else {
        $env:PROFILE = "local"
        Push-Location $RepoRoot
        try {
            Invoke-Native $Py @("-m", "mlcicd.training.train")
            Invoke-Native $Py @("-m", "mlcicd.training.evaluate")
            Invoke-Native $Py @("-m", "mlcicd.registry.register")
        }
        finally { Pop-Location }
    }
}

Write-Host "== 4. Start app, Prometheus and Grafana"
$upArgs = @("compose", "-f", $Compose, "up", "-d")
if (-not $NoBuild) { $upArgs += "--build" }
Invoke-Native docker ($upArgs + @("app", "prometheus", "grafana"))
Wait-Http "http://localhost:8000/health" 120

Write-Host ""
Write-Host "Local stack is up."
Write-Host "  API docs   : http://localhost:8000/docs"
Write-Host "  MLflow     : http://localhost:5000"
Write-Host "  Prometheus : http://localhost:9090/targets"
Write-Host "  Grafana    : http://localhost:3000  (admin / admin)"
Write-Host "  Streamlit  : .\.venv-ui\Scripts\streamlit run ui/streamlit_app.py"
