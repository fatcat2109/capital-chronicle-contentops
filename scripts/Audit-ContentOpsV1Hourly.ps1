# Independent read-only hourly audit runner.  It performs no model/provider/public call,
# browser automation, control mutation, restart, repair, or reconciliation.
[CmdletBinding()]
param()

$ErrorActionPreference = 'Stop'
$repoRoot = Split-Path -Parent $PSScriptRoot
$productionStore = 'A:\Capital Chronicle\Runtime\ContentOps\contentops_daily_app_v1.sqlite3'
$auditRoot = 'A:\Capital Chronicle\Runtime\ContentOps\hourly_audit'
$runnerLog = Join-Path $auditRoot 'audit_runner.log'

$python = Get-Command python -ErrorAction SilentlyContinue
if (-not $python) { throw 'PYTHON_NOT_FOUND_FOR_HOURLY_AUDIT' }
New-Item -ItemType Directory -Path $auditRoot -Force | Out-Null

Push-Location $repoRoot
try {
    $result = & $python.Source -m live_contentops.hourly_runtime_audit_v1 `
        --store $productionStore --repo-root $repoRoot 2>&1
    $exitCode = $LASTEXITCODE
} finally {
    Pop-Location
}

$safeLine = (($result -join ' ') -replace '(?i)(authorization|token|secret|password|api[_-]?key)\s*[:=]\s*\S+', '$1=[REDACTED]')
$timestamp = [DateTime]::UtcNow.ToString('o')
[IO.File]::AppendAllText($runnerLog, "$timestamp $safeLine$([Environment]::NewLine)", [Text.UTF8Encoding]::new($false))
Write-Output $safeLine
exit $exitCode
