[CmdletBinding()]
param(
    [string]$TaskName = 'CapitalChronicle_ContentOps_V1_Simple_Scheduler',
    [int]$PollSeconds = 60,
    [switch]$NoStart
)

$ErrorActionPreference = 'Stop'
$repoRoot = (Resolve-Path -LiteralPath (Join-Path $PSScriptRoot '..')).Path
$runtimeRoot = 'A:\Capital Chronicle\Runtime\ContentOps'
$python = (Resolve-Path -LiteralPath (Join-Path $runtimeRoot 'v1-runtime\venv\Scripts\python.exe')).Path
$runner = (Resolve-Path -LiteralPath (Join-Path $repoRoot 'scripts\run_v1_simple_gemini_scheduler.py')).Path
$schedulerRoot = (Resolve-Path -LiteralPath (Join-Path $runtimeRoot 'simple_gemini_scheduler_v1')).Path
$store = (Resolve-Path -LiteralPath (Join-Path $runtimeRoot 'contentops_daily_app_v1.sqlite3')).Path
$output = (Resolve-Path -LiteralPath (Join-Path $runtimeRoot 'daily_app_outputs')).Path

$arguments = ('"{0}" --scheduler-root "{1}" --published-memory-store "{2}" --published-memory-output-root "{3}" --run-forever --poll-seconds {4}' -f $runner, $schedulerRoot, $store, $output, $PollSeconds)
$action = New-ScheduledTaskAction -Execute $python -Argument $arguments -WorkingDirectory $repoRoot
$operator = [System.Security.Principal.WindowsIdentity]::GetCurrent().Name
$atLogon = New-ScheduledTaskTrigger -AtLogOn -User $operator
$watchdog = New-ScheduledTaskTrigger -Once -At (Get-Date).AddMinutes(1) `
    -RepetitionInterval (New-TimeSpan -Minutes 5) `
    -RepetitionDuration (New-TimeSpan -Days 3650)
$principal = New-ScheduledTaskPrincipal -UserId $operator -LogonType Interactive -RunLevel Limited
$settings = New-ScheduledTaskSettingsSet -MultipleInstances IgnoreNew -StartWhenAvailable `
    -RestartCount 999 -RestartInterval (New-TimeSpan -Minutes 1) `
    -ExecutionTimeLimit (New-TimeSpan -Seconds 0)

Register-ScheduledTask -TaskName $TaskName -Action $action -Trigger @($atLogon, $watchdog) `
    -Principal $principal -Settings $settings `
    -Description 'Single host owner for the canonical Capital Chronicle V1 Simple scheduler.' `
    -Force | Out-Null
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
    canonical_scheduler_root = $schedulerRoot
    exactly_one_task_owner = $true
    public_write_performed = $false
} | ConvertTo-Json -Depth 4
