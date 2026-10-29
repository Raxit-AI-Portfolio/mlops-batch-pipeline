[CmdletBinding()]
param(
    [switch]$Volumes
)

$ErrorActionPreference = "Stop"
$RepoRoot = Split-Path -Parent $PSScriptRoot
$Compose = Join-Path $RepoRoot "infra\docker-compose.yml"
. (Join-Path $PSScriptRoot "common.ps1")

$downArgs = @("compose", "-f", $Compose, "down")
if ($Volumes) { $downArgs += "-v" }
Invoke-Native docker $downArgs

Write-Host "Local stack stopped."
Write-Host "The MLflow registry lives inside the container, so the next local-up.ps1 re-seeds the model."
if ($Volumes) { Write-Host "Volumes removed too (fake-gcs data, registry images)." }
