# Explicit operator resume for the persistent ContentOps text-model cost fuse.
[CmdletBinding()]
param()

$ErrorActionPreference = 'Stop'
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
