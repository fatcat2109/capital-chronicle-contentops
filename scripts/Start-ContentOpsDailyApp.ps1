# One-click launch/resume helper for the Capital Chronicle ContentOps V1 Daily App.
# This file is a thin shell: all decisions happen in live_contentops.daily_app_launcher_v1.
# It performs no public writes, reads no secrets, and never kills processes.

$ErrorActionPreference = 'Stop'

$RepoRoot = Split-Path -Parent $PSScriptRoot
. (Join-Path $PSScriptRoot 'Resolve-ContentOpsV1Runtime.ps1')
$Python = Resolve-ContentOpsV1Runtime

Write-Output 'Capital Chronicle ContentOps V1 - one-click morning launcher'
Write-Output ("Repo: " + $RepoRoot)
Write-Output ("Python: " + $Python)
Write-Output ''

$launcherArgs = @('-m', 'live_contentops.daily_app_launcher_v1') + @($args | Where-Object { $_ })

Push-Location $RepoRoot
try {
    & $Python -m live_contentops.v1_runtime_preflight_v1 | Out-Host
    if ($LASTEXITCODE -ne 0) { throw 'CONTENTOPS_V1_RUNTIME_PREFLIGHT_FAILED' }
    & $Python @launcherArgs
    $exitCode = $LASTEXITCODE
} finally {
    Pop-Location
}

Write-Output ''
Write-Output 'Launcher finished. The Daily App (if started) keeps running independently.'
exit $exitCode
