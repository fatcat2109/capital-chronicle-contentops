# One-click launch/resume helper for the Capital Chronicle ContentOps V1 Daily App.
# This file is a thin shell: all decisions happen in live_contentops.daily_app_launcher_v1.
# It performs no public writes, reads no secrets, and never kills processes.

$ErrorActionPreference = 'Stop'

$RepoRoot = Split-Path -Parent $PSScriptRoot

function Resolve-Python {
    foreach ($candidate in @('python', 'py', 'python3')) {
        $command = Get-Command $candidate -ErrorAction SilentlyContinue
        if ($command) { return $command.Source }
    }
    throw 'PYTHON_NOT_FOUND: install Python 3 and re-run.'
}

$Python = Resolve-Python

Write-Output 'Capital Chronicle ContentOps V1 - one-click morning launcher'
Write-Output ("Repo: " + $RepoRoot)
Write-Output ("Python: " + $Python)
Write-Output ''

$launcherArgs = @('-m', 'live_contentops.daily_app_launcher_v1') + @($args | Where-Object { $_ })

Push-Location $RepoRoot
try {
    & $Python @launcherArgs
    $exitCode = $LASTEXITCODE
} finally {
    Pop-Location
}

Write-Output ''
Write-Output 'Launcher finished. The Daily App (if started) keeps running independently.'
exit $exitCode
