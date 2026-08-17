# Idempotently creates the stable ContentOps-owned V1 runtime. Never targets a Codex cache.
[CmdletBinding()]
param()

$ErrorActionPreference = 'Stop'
$RepoRoot = Split-Path -Parent $PSScriptRoot
$RuntimeRoot = 'A:\Capital Chronicle\Runtime\ContentOps\v1-runtime'
$VenvRoot = Join-Path $RuntimeRoot 'venv'
$VenvPython = Join-Path $VenvRoot 'Scripts\python.exe'
$Requirements = Join-Path $RepoRoot 'requirements-v1-runtime.txt'

if ($VenvRoot -like '*\.cache\codex-runtimes\*') {
    throw 'CODEX_PRIVATE_CACHE_RUNTIME_FORBIDDEN'
}

if (-not (Test-Path -LiteralPath $VenvPython -PathType Leaf)) {
    $BasePython = 'C:\Users\bullw\AppData\Local\Programs\Python\Python313\python.exe'
    if (-not (Test-Path -LiteralPath $BasePython -PathType Leaf)) {
        throw 'STABLE_PYTHON_313_NOT_FOUND'
    }
    New-Item -ItemType Directory -Path $RuntimeRoot -Force | Out-Null
    & $BasePython -m venv $VenvRoot
    if ($LASTEXITCODE -ne 0) { throw 'V1_RUNTIME_VENV_CREATION_FAILED' }
}

& $VenvPython -m pip install --disable-pip-version-check -r $Requirements
if ($LASTEXITCODE -ne 0) { throw 'V1_RUNTIME_DEPENDENCY_INSTALL_FAILED' }

Push-Location $RepoRoot
try {
    & $VenvPython -m live_contentops.v1_runtime_preflight_v1
    if ($LASTEXITCODE -ne 0) { throw 'V1_RUNTIME_PREFLIGHT_FAILED' }
} finally {
    Pop-Location
}

Write-Output $VenvPython
