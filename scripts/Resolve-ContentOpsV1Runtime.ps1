function Resolve-ContentOpsV1Runtime {
    $candidate = 'A:\Capital Chronicle\Runtime\ContentOps\v1-runtime\venv\Scripts\python.exe'
    if (-not (Test-Path -LiteralPath $candidate -PathType Leaf)) {
        throw 'CONTENTOPS_V1_RUNTIME_NOT_INITIALIZED: run scripts\Initialize-ContentOpsV1Runtime.ps1'
    }
    if ($candidate -like '*\.cache\codex-runtimes\*') {
        throw 'CODEX_PRIVATE_CACHE_RUNTIME_FORBIDDEN'
    }
    return $candidate
}
