function Invoke-Native {
    param([string]$Exe, [string[]]$Arguments)
    & $Exe @Arguments
    if ($LASTEXITCODE -ne 0) { throw "$Exe $($Arguments -join ' ') failed (exit $LASTEXITCODE)" }
}

function Get-NativeOutput {
    param([string]$Exe, [string[]]$Arguments)
    $prev = $ErrorActionPreference
    $ErrorActionPreference = "Continue"
    try { $out = & $Exe @Arguments 2>$null } finally { $ErrorActionPreference = $prev }
    $script:LastNativeExit = $LASTEXITCODE
    $out
}

function Confirm-Step([string]$Message) {
    if ($Yes) { return }
    if ((Read-Host "$Message (y/N)") -notmatch '^[yY]') { throw "Aborted by user." }
}

function Get-LocalSetting([string]$Name) {
    $fromEnv = [Environment]::GetEnvironmentVariable($Name)
    if ($fromEnv) { return $fromEnv }
    $file = Join-Path $RepoRoot ".env"
    if (Test-Path $file) {
        $line = Get-Content $file | Where-Object { $_ -match "^\s*$Name\s*=" } | Select-Object -First 1
        if ($line) { return ($line -split '=', 2)[1].Trim().Trim('"') }
    }
    throw "$Name is not set. Add '$Name=<value>' to .env (gitignored, see .env.example) or set `$env:$Name."
}

function Backup-State {
    $dir = Get-LocalSetting "GCP_BACKUP_DIR"
    if (-not (Test-Path $dir)) { New-Item -ItemType Directory -Path $dir -Force | Out-Null }
    $dest = Join-Path $dir ("terraform.tfstate." + (Get-Date -Format "yyyyMMdd-HHmmss"))
    Copy-Item (Join-Path $TfDir "terraform.tfstate") $dest
    Write-Host "State backup: $dest"
}
