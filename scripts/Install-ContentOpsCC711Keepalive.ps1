<#
.SYNOPSIS
CC-711 ContentOps Task Scheduler registration helper for X_List_Feed PT15M keepalive
and BrowserOS Neo health/cold-start probe.

.DESCRIPTION
Defaults strictly to -DryRun (zero live Windows Task Scheduler mutations).
Validates the committed XML templates (Enabled=false, UserId=JP,
LogonType=InteractiveToken, MultipleInstancesPolicy=IgnoreNew, PT15M repeat)
and prints the exact plan as JSON.

Pass -Apply ONLY during an approved Ops installation window to register the
disabled tasks (<Enabled>false</Enabled>). Tasks remain disabled until Ops
explicitly enables them via Enable-ScheduledTask.
#>
[CmdletBinding()]
param(
    [ValidateSet('All', 'XFeed', 'NeoHealth')]
    [string]$Target = 'All',
    [switch]$Apply,
    [switch]$DryRun
)

$ErrorActionPreference = 'Stop'
$isDryRun = (-not $Apply.IsPresent) -or $DryRun.IsPresent
$repoRoot = (Resolve-Path -LiteralPath (Join-Path $PSScriptRoot '..')).Path
$xmlDir = Join-Path $repoRoot 'config\task_scheduler'

$specs = @(
    [pscustomobject]@{
        key = 'XFeed'
        task_name = 'CapitalChronicle_ContentOps_X_List_Feed'
        xml_path = Join-Path $xmlDir 'CapitalChronicle_ContentOps_X_List_Feed_Keepalive_CC711.xml'
    },
    [pscustomobject]@{
        key = 'NeoHealth'
        task_name = 'CapitalChronicle_ContentOps_BrowserOS_Neo_Health'
        xml_path = Join-Path $xmlDir 'CapitalChronicle_ContentOps_BrowserOS_Neo_Health_CC711.xml'
    }
)

if ($Target -ne 'All') {
    $specs = @($specs | Where-Object { $_.key -eq $Target })
}

$results = @()
foreach ($spec in $specs) {
    if (-not (Test-Path -LiteralPath $spec.xml_path -PathType Leaf)) {
        throw "CC711_TASK_XML_MISSING: $($spec.xml_path)"
    }
    $rawXml = Get-Content -LiteralPath $spec.xml_path -Raw -Encoding UTF8
    [xml]$doc = $rawXml
    $ns = New-Object System.Xml.XmlNamespaceManager($doc.NameTable)
    $ns.AddNamespace('t', 'http://schemas.microsoft.com/windows/2004/02/mit/task')

    $uri = ($doc.SelectSingleNode('/t:Task/t:RegistrationInfo/t:URI', $ns)).InnerText.Trim()
    $userId = ($doc.SelectSingleNode('/t:Task/t:Principals/t:Principal/t:UserId', $ns)).InnerText.Trim()
    $logonType = ($doc.SelectSingleNode('/t:Task/t:Principals/t:Principal/t:LogonType', $ns)).InnerText.Trim()
    $enabled = ($doc.SelectSingleNode('/t:Task/t:Settings/t:Enabled', $ns)).InnerText.Trim()
    $multi = ($doc.SelectSingleNode('/t:Task/t:Settings/t:MultipleInstancesPolicy', $ns)).InnerText.Trim()
    $interval = ($doc.SelectSingleNode('/t:Task/t:Triggers/t:TimeTrigger/t:Repetition/t:Interval', $ns)).InnerText.Trim()

    if ($uri -ne ('\' + $spec.task_name)) { throw "CC711_XML_URI_MISMATCH: $uri" }
    if ($userId -ne 'JP') { throw "CC711_XML_USERID_MISMATCH: $userId" }
    if ($logonType -ne 'InteractiveToken') { throw "CC711_XML_LOGONTYPE_MISMATCH: $logonType" }
    if ($enabled -ne 'false') { throw "CC711_XML_ENABLED_MUST_BE_FALSE: $enabled" }
    if ($multi -ne 'IgnoreNew') { throw "CC711_XML_MULTIPLE_INSTANCES_MISMATCH: $multi" }
    if ($interval -ne 'PT15M') { throw "CC711_XML_INTERVAL_MISMATCH: $interval" }

    # Read-only in-memory Task Scheduler COM XML parser check (zero live Task Scheduler mutations).
    $comSvc = New-Object -ComObject 'Schedule.Service'
    $comDef = $comSvc.NewTask(0)
    $comDef.XmlText = $rawXml
    if ($comDef.Settings.Enabled) { throw "CC711_COM_XML_ENABLED_MUST_BE_FALSE" }
    if ($comDef.Principal.UserId -ne 'JP') { throw "CC711_COM_XML_USERID_MISMATCH: $($comDef.Principal.UserId)" }
    if ($comDef.Principal.LogonType -ne 3) { throw "CC711_COM_XML_LOGONTYPE_MISMATCH: $($comDef.Principal.LogonType)" }
    if ($comDef.Triggers.Count -lt 2) { throw "CC711_COM_XML_TRIGGERS_MISSING: $($comDef.Triggers.Count)" }

    if ($isDryRun) {
        $actionState = 'DRY_RUN_VALIDATED_NO_MUTATION'
    } else {
        Register-ScheduledTask -TaskName $spec.task_name -Xml $rawXml -Force | Out-Null
        $actionState = 'REGISTERED_DISABLED'
    }

    $results += [pscustomobject]@{
        task_name = $spec.task_name
        xml_path = $spec.xml_path
        uri = $uri
        user_id = $userId
        logon_type = $logonType
        enabled = ($enabled -eq 'true')
        repeat_interval = $interval
        multiple_instances_policy = $multi
        com_xml_validated = $true
        action = $actionState
    }
}

[pscustomobject]@{
    schema_version = 'contentops.cc711_task_installer.v1'
    dry_run = $isDryRun
    live_task_mutated = (-not $isDryRun)
    public_write_performed = $false
    tasks = $results
} | ConvertTo-Json -Depth 5
