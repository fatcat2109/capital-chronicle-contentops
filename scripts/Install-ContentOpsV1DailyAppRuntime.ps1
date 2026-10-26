[CmdletBinding()]
param(
    [string]$TaskName = 'CapitalChronicle_ContentOps_V1_Daily_App_Runtime',
    [int]$PollSeconds = 60,
    [int]$ApiPort = 8765,
    [switch]$NoStart,
    [switch]$UpdateExistingOnly
)

$ErrorActionPreference = 'Stop'
$repoRoot = (Resolve-Path -LiteralPath (Join-Path $PSScriptRoot '..')).Path
$runtimeRoot = 'A:\Capital Chronicle\Runtime\ContentOps'
$python = (Resolve-Path -LiteralPath (Join-Path $runtimeRoot 'v1-runtime\venv\Scripts\python.exe')).Path
$pythonw = (Resolve-Path -LiteralPath (Join-Path $runtimeRoot 'v1-runtime\venv\Scripts\pythonw.exe')).Path
$store = (Resolve-Path -LiteralPath (Join-Path $runtimeRoot 'contentops_daily_app_v1.sqlite3')).Path
$output = (Resolve-Path -LiteralPath (Join-Path $runtimeRoot 'daily_app_outputs')).Path

Push-Location $repoRoot
try {
    & $python -m live_contentops.v1_runtime_preflight_v1 | Out-Null
    if ($LASTEXITCODE -ne 0) { throw 'CONTENTOPS_V1_RUNTIME_PREFLIGHT_FAILED' }
} finally {
    Pop-Location
}

$entry = "import sys;from live_contentops.daily_app_launcher_v1 import run_scheduled_daily_app;sys.argv[0]='live_contentops.cli';run_scheduled_daily_app()"
$arguments = ('-c "{0}" daily-app start --store-path "{1}" --output-root "{2}" --api-port {3} --poll-seconds {4}' -f $entry, $store, $output, $ApiPort, $PollSeconds)
$action = New-ScheduledTaskAction -Execute $pythonw -Argument $arguments -WorkingDirectory $repoRoot
$existing = Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue
if ($UpdateExistingOnly -and -not $existing) { throw 'CONTENTOPS_EXISTING_RUNTIME_TASK_REQUIRED' }
$operator = [System.Security.Principal.WindowsIdentity]::GetCurrent().Name
$atLogon = New-ScheduledTaskTrigger -AtLogOn -User $operator
$watchdog = New-ScheduledTaskTrigger -Once -At (Get-Date).AddMinutes(1) `
    -RepetitionInterval (New-TimeSpan -Minutes 5) `
    -RepetitionDuration (New-TimeSpan -Days 3650)
$principal = New-ScheduledTaskPrincipal -UserId $operator -LogonType Interactive -RunLevel Limited
$settings = New-ScheduledTaskSettingsSet -MultipleInstances IgnoreNew -StartWhenAvailable `
    -RestartCount 999 -RestartInterval (New-TimeSpan -Minutes 1) `
    -ExecutionTimeLimit (New-TimeSpan -Seconds 0) -Hidden

if ($existing) {
    # Restore this same owner without resetting its accepted triggers or principal.
    $existingSettings = $existing.Settings
    $existingSettings.Hidden = $true
    $existingSettings.Enabled = $true
    Set-ScheduledTask -TaskName $TaskName -Action $action -Settings $existingSettings | Out-Null
} else {
    Register-ScheduledTask -TaskName $TaskName -Action $action -Trigger @($atLogon, $watchdog) `
        -Principal $principal -Settings $settings `
        -Description 'Persistent V1 intake/state/API owner; four native Codex Desktop tasks own routine editorial work.' `
        -Force | Out-Null
}
if (-not $NoStart) {
    Start-ScheduledTask -TaskName $TaskName
}

$task = Get-ScheduledTask -TaskName $TaskName
$info = $task | Get-ScheduledTaskInfo
[pscustomobject]@{
    task_name = $task.TaskName
    state = [string]$task.State
    last_run_time = $info.LastRunTime
    last_task_result = $info.LastTaskResult
    trigger_count = @($task.Triggers).Count
    executable = $task.Actions[0].Execute
    working_directory = $task.Actions[0].WorkingDirectory
    canonical_store = $store
    routine_editorial_owner = 'NATIVE_CODEX_DESKTOP'
    daily_app_routine_editorial_execution = $false
    exactly_one_daily_app_runtime_owner = $true
    public_write_performed = $false
} | ConvertTo-Json -Depth 4
