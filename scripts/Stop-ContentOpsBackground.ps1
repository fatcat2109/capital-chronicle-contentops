# One-click ContentOps background shutdown. The persistent LLM fuse is activated before
# process inventory so a surviving process cannot begin another 9Router text-model request.
[CmdletBinding()]
param()

$ErrorActionPreference = 'Stop'
$controlRoot = 'A:\Capital Chronicle\Runtime\ContentOps\control'
$pauseMarker = Join-Path $controlRoot 'llm_operator_pause.flag'
$productionStore = 'A:\Capital Chronicle\Runtime\ContentOps\contentops_daily_app_v1.sqlite3'
$canonicalRoots = @(
    'A:\Capital Chronicle\ContentOps',
    'A:\Capital Chronicle\Worktrees\ContentOps',
    'A:\Capital Chronicle\Runtime\ContentOps'
)

# COST-SAFETY ORDERING INVARIANT: activate the durable fuse before inventory or termination.
New-Item -ItemType Directory -Path $controlRoot -Force | Out-Null
$pausePayload = [ordered]@{
    schema_version = 'contentops.llm_operator_control.v1'
    state = 'PAUSED_BY_OPERATOR'
    reason = 'EMERGENCY_COST_SAFETY_STOP'
    activated_at_utc = [DateTime]::UtcNow.ToString('o')
    contains_secrets = $false
} | ConvertTo-Json -Compress
$temporaryMarker = "$pauseMarker.$PID.tmp"
[IO.File]::WriteAllText($temporaryMarker, $pausePayload + [Environment]::NewLine, [Text.UTF8Encoding]::new($false))
Move-Item -LiteralPath $temporaryMarker -Destination $pauseMarker -Force
if (-not (Test-Path -LiteralPath $pauseMarker)) {
    throw 'LLM_PAUSE_ACTIVATION_FAILED: no process termination was attempted.'
}

function Test-CanonicalPathMarker([string]$commandLine) {
    foreach ($root in $canonicalRoots) {
        if ($commandLine.IndexOf($root, [StringComparison]::OrdinalIgnoreCase) -ge 0) {
            return $true
        }
    }
    return $false
}

function Test-ProvenContentOpsBackgroundProcess($process) {
    $name = ([string]$process.Name).ToLowerInvariant()
    $commandLine = [string]$process.CommandLine
    if ([string]::IsNullOrWhiteSpace($commandLine)) { return $false }
    if ($name -in @('chrome.exe', 'msedge.exe', 'git.exe', 'explorer.exe')) { return $false }

    $hasCanonicalPath = Test-CanonicalPathMarker $commandLine
    $isCanonicalDailyApp = (
        $name -in @('python.exe', 'pythonw.exe') -and
        $commandLine -match '(?i)live_contentops[./\\]cli' -and
        $commandLine -match '(?i)daily-app' -and
        $commandLine -match '(?i)\bstart\b|--run-forever' -and
        $commandLine -match '(?i)contentops_daily_app_v1\.sqlite3'
    )
    $isCanonicalPythonWorker = (
        $name -in @('python.exe', 'pythonw.exe') -and
        $hasCanonicalPath -and
        $commandLine -match '(?i)(live_contentops[./\\](server|nine_router_preflight_v2)|rolling_x|production_orchestrator|daily_app|tier2_video_factory|run_direct_image_bakeoff)'
    )
    $isV5NodeWorker = (
        $name -in @('node.exe', 'cmd.exe') -and
        $hasCanonicalPath -and
        $commandLine -match '(?i)ui[\\/]contentops_v5' -and
        $commandLine -match '(?i)(vite|npm\s+run\s+(dev|preview))'
    )
    $isContentOpsRenderWorker = (
        $name -in @('ffmpeg.exe', 'node.exe', 'python.exe', 'pythonw.exe') -and
        $hasCanonicalPath -and
        $commandLine -match '(?i)(tier2|render|remotion|daily_app_outputs)'
    )
    return $isCanonicalDailyApp -or $isCanonicalPythonWorker -or $isV5NodeWorker -or $isContentOpsRenderWorker
}

$allProcesses = @(Get-CimInstance Win32_Process)
$byPid = @{}
foreach ($process in $allProcesses) { $byPid[[int]$process.ProcessId] = $process }

# Protect this script and its complete parent lineage.
$protectedPids = [Collections.Generic.HashSet[int]]::new()
$cursor = [int]$PID
while ($cursor -gt 0 -and $byPid.ContainsKey($cursor) -and $protectedPids.Add($cursor)) {
    $cursor = [int]$byPid[$cursor].ParentProcessId
}

$provenPids = [Collections.Generic.HashSet[int]]::new()
foreach ($process in $allProcesses) {
    $candidatePid = [int]$process.ProcessId
    if (-not $protectedPids.Contains($candidatePid) -and (Test-ProvenContentOpsBackgroundProcess $process)) {
        [void]$provenPids.Add($candidatePid)
    }
}

# Include descendants of proven roots, except persistent browsers and protected operator lineage.
$changed = $true
while ($changed) {
    $changed = $false
    foreach ($process in $allProcesses) {
        $candidatePid = [int]$process.ProcessId
        $parentPid = [int]$process.ParentProcessId
        $name = ([string]$process.Name).ToLowerInvariant()
        if ($provenPids.Contains($parentPid) -and
            -not $provenPids.Contains($candidatePid) -and
            -not $protectedPids.Contains($candidatePid) -and
            $name -notin @('chrome.exe', 'msedge.exe')) {
            [void]$provenPids.Add($candidatePid)
            $changed = $true
        }
    }
}

# Stop child processes before their proven parents. No command lines are printed.
$orderedPids = @($provenPids) | Sort-Object {
    $depth = 0
    $cursorPid = [int]$_
    while ($byPid.ContainsKey($cursorPid) -and $depth -lt 32) {
        $cursorPid = [int]$byPid[$cursorPid].ParentProcessId
        $depth++
    }
    -$depth
}
$stoppedCount = 0
foreach ($targetPid in $orderedPids) {
    if (Get-Process -Id $targetPid -ErrorAction SilentlyContinue) {
        Stop-Process -Id $targetPid -Force
        $stoppedCount++
    }
}

Start-Sleep -Milliseconds 400
$remainingProven = @($orderedPids | Where-Object { Get-Process -Id $_ -ErrorAction SilentlyContinue })
$dailyListeners = @(Get-NetTCPConnection -LocalPort 5174 -State Listen -ErrorAction SilentlyContinue)
$v5Listeners = @(
    @(Get-NetTCPConnection -LocalPort 4173 -State Listen -ErrorAction SilentlyContinue) +
    @(Get-NetTCPConnection -LocalPort 5173 -State Listen -ErrorAction SilentlyContinue)
)

$sqliteIntegrity = 'UNAVAILABLE'
if (Test-Path -LiteralPath $productionStore) {
    $python = Get-Command python -ErrorAction SilentlyContinue
    if ($python) {
        $sqliteIntegrity = & $python.Source -c "import sqlite3; c=sqlite3.connect(r'$productionStore'); print(c.execute('PRAGMA integrity_check').fetchone()[0]); c.close()"
        if ($LASTEXITCODE -ne 0) { $sqliteIntegrity = 'CHECK_FAILED' }
    }
} else {
    $sqliteIntegrity = 'STORE_MISSING'
}

$pauseActive = Test-Path -LiteralPath $pauseMarker
$success = $pauseActive -and $remainingProven.Count -eq 0 -and $dailyListeners.Count -eq 0 -and $v5Listeners.Count -eq 0 -and $sqliteIntegrity -eq 'ok'

Write-Output ('CONTENTOPS BACKGROUND: ' + $(if ($remainingProven.Count -eq 0 -and $dailyListeners.Count -eq 0 -and $v5Listeners.Count -eq 0) { 'STOPPED' } else { 'ATTENTION REQUIRED' }))
Write-Output ('LLM NETWORK CALLS: ' + $(if ($pauseActive) { 'PAUSED BY OPERATOR' } else { 'PAUSE FAILED' }))
Write-Output ('DAILY APP: ' + $(if ($dailyListeners.Count -eq 0) { 'STOPPED' } else { 'LISTENER REMAINS' }))
Write-Output ('V5 RUNTIME: ' + $(if ($v5Listeners.Count -eq 0) { 'STOPPED' } else { 'LISTENER REMAINS' }))
Write-Output ("PROVEN BACKGROUND PROCESSES STOPPED: $stoppedCount")
Write-Output ('PRODUCTION STORE: ' + $(if ($sqliteIntegrity -eq 'ok') { 'PRESERVED / OK' } else { "PRESERVED / $sqliteIntegrity" }))
Write-Output 'CHROME INGESTION PROFILE: PRESERVED'
Write-Output 'EDGE PUBLISHING PROFILE: PRESERVED'
Write-Output 'AMBIGUOUS PROCESSES: NOT KILLED'

if (-not $success) { exit 2 }
exit 0
