# One-click launcher for the nontechnical ContentOps V1 run monitor.
# The canonical launcher owns runtime decisions. This wrapper only selects the simple UI route.

[CmdletBinding()]
param(
    [switch]$NoOpen
)

$ErrorActionPreference = 'Stop'
$RepoRoot = Split-Path -Parent $PSScriptRoot
$CanonicalLauncher = Join-Path $PSScriptRoot 'Start-ContentOpsDailyApp.ps1'

Write-Output 'Capital Chronicle ContentOps V1 - Simple Run Monitor'
Write-Output ''

& $CanonicalLauncher --no-open-browser
if ($LASTEXITCODE -ne 0) { throw 'CONTENTOPS_DAILY_APP_START_FAILED' }

$dashboardUrl = $null
foreach ($port in @(4173, 5173)) {
    $candidate = "http://127.0.0.1:$port/?view=simple"
    try {
        $response = Invoke-WebRequest -UseBasicParsing -Uri "http://127.0.0.1:$port/" -TimeoutSec 2
        if ($response.StatusCode -eq 200) {
            $dashboardUrl = $candidate
            break
        }
    } catch {
        continue
    }
}

if (-not $dashboardUrl) { throw 'SIMPLE_RUN_DASHBOARD_NOT_READY' }

if ($NoOpen) {
    Write-Output ("Simple Run Monitor ready: " + $dashboardUrl)
} else {
    Start-Process $dashboardUrl
    Write-Output ("Simple Run Monitor opened: " + $dashboardUrl)
}
exit 0
