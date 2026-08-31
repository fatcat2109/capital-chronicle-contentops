[CmdletBinding()]
param(
    [string]$TaskName = 'CapitalChronicle_ContentOps_V1_Daily_App_Runtime',
    [int]$PollSeconds = 60,
    [int]$ApiPort = 8765,
    [switch]$NoStart
)

$ErrorActionPreference = 'Stop'
$repoRoot = (Resolve-Path -LiteralPath (Join-Path $PSScriptRoot '..')).Path
$runtimeRoot = 'A:\Capital Chronicle\Runtime\ContentOps'
$python = (Resolve-Path -LiteralPath (Join-Path $runtimeRoot 'v1-runtime\venv\Scripts\python.exe')).Path
$store = (Resolve-Path -LiteralPath (Join-Path $runtimeRoot 'contentops_daily_app_v1.sqlite3')).Path
$output = (Resolve-Path -LiteralPath (Join-Path $runtimeRoot 'daily_app_outputs')).Path

Push-Location $repoRoot
try {
    & $python -m live_contentops.v1_runtime_preflight_v1 | Out-Null
    if ($LASTEXITCODE -ne 0) { throw 'CONTENTOPS_V1_RUNTIME_PREFLIGHT_FAILED' }
} finally {
    Pop-Location
}

$arguments = ('-m live_contentops.cli daily-app start --store-path "{0}" --output-root "{1}" --api-port {2} --poll-seconds {3}' -f $store, $output, $ApiPort, $PollSeconds)
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
    -Description 'Persistent owner for the existing V1 Daily App intake, state, and loopback API runtime; Simple remains the sole routine editorial scheduler.' `
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
    canonical_store = $store
    routine_editorial_owner = 'SIMPLE_GEMINI_RUNTIME'
    daily_app_routine_editorial_execution = $false
    exactly_one_daily_app_runtime_owner = $true
    public_write_performed = $false
} | ConvertTo-Json -Depth 4
