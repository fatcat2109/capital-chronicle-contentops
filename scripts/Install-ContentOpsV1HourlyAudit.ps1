# Install/update the canonical V1 hourly audit for the current interactive operator.
# No password, elevation, provider call, or public-write authority is requested.
[CmdletBinding()]
param()

$ErrorActionPreference = 'Stop'
$taskName = 'CapitalChronicle_ContentOps_V1_Hourly_Audit'
$auditScript = (Join-Path $PSScriptRoot 'Audit-ContentOpsV1Hourly.ps1')
if (-not (Test-Path -LiteralPath $auditScript)) { throw 'HOURLY_AUDIT_SCRIPT_MISSING' }

$operator = [Security.Principal.WindowsIdentity]::GetCurrent().Name
$actionArguments = '-NoProfile -ExecutionPolicy Bypass -File "' + $auditScript + '"'
$action = New-ScheduledTaskAction -Execute 'powershell.exe' -Argument $actionArguments -WorkingDirectory (Split-Path -Parent $PSScriptRoot)
$trigger = New-ScheduledTaskTrigger -Once -At (Get-Date).AddMinutes(2) `
    -RepetitionInterval (New-TimeSpan -Hours 1) `
    -RepetitionDuration (New-TimeSpan -Days 3650)
$principal = New-ScheduledTaskPrincipal -UserId $operator -LogonType Interactive -RunLevel Limited
$settings = New-ScheduledTaskSettingsSet -MultipleInstances IgnoreNew -StartWhenAvailable -ExecutionTimeLimit (New-TimeSpan -Minutes 10)

Register-ScheduledTask -TaskName $taskName -Action $action -Trigger $trigger -Principal $principal -Settings $settings -Description 'Read-only ContentOps V1 hourly runtime audit; audit artifact writes only.' -Force | Out-Null
$task = Get-ScheduledTask -TaskName $taskName
$info = Get-ScheduledTaskInfo -TaskName $taskName
[ordered]@{
    task_name = $taskName
    state = [string]$task.State
    operator = $operator
    logon_type = 'Interactive'
    run_level = 'Limited'
    next_run_utc = $info.NextRunTime.ToUniversalTime().ToString('o')
    action_script = $auditScript
    password_supplied = $false
} | ConvertTo-Json -Compress
