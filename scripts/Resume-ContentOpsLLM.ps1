# Explicit operator resume for the persistent ContentOps text-model cost fuse.
[CmdletBinding()]
param()

$ErrorActionPreference = 'Stop'
throw 'Use the audited native Desktop rollout transition. Clearing this fuse alone does not validate the four task model/prompt bindings or retire legacy schedulers.'
$controlRoot = 'A:\Capital Chronicle\Runtime\ContentOps\control'
$pauseMarker = Join-Path $controlRoot 'llm_operator_pause.flag'

if (Test-Path -LiteralPath $pauseMarker) {
    Remove-Item -LiteralPath $pauseMarker -Force
}

if (Test-Path -LiteralPath $pauseMarker) {
    Write-Output 'LLM EXECUTION: STILL PAUSED (marker could not be cleared)'
    exit 2
}

Write-Output 'LLM EXECUTION: ENABLED BY EXPLICIT OPERATOR ACTION'
Write-Output 'DAILY APP: NOT STARTED'
Write-Output 'Use Start_ContentOps_Daily_App.cmd separately when startup is intended.'
exit 0
