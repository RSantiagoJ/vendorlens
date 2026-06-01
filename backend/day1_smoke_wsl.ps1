param(
    [switch]$RebuildIndex
)

$ErrorActionPreference = "Stop"
$wslExe = Join-Path $env:WINDIR "System32\wsl.exe"

if (-not (Test-Path $wslExe)) {
    throw "wsl.exe not found at $wslExe"
}

# Convert backend Windows path to Linux path for WSL --cd.
$backendWindowsPath = $PSScriptRoot -replace "\\", "/"
$backendLinuxPath = (& $wslExe wslpath -a $backendWindowsPath).Trim()

if (-not $backendLinuxPath) {
    throw "Could not resolve backend path in WSL."
}

Write-Host "Using backend path in WSL: $backendLinuxPath"
& $wslExe -d Ubuntu --cd $backendLinuxPath .venv-wsl311/bin/python --version

if ($RebuildIndex) {
    Write-Host "Rebuilding vector index..."
    & $wslExe -d Ubuntu --cd $backendLinuxPath .venv-wsl311/bin/python ingest.py --force
}

Write-Host "Running Day 1 RAG checkpoint..."
& $wslExe -d Ubuntu --cd $backendLinuxPath .venv-wsl311/bin/python test_rag.py

if ($LASTEXITCODE -ne 0) {
    throw "Day 1 smoke check failed with exit code $LASTEXITCODE"
}

Write-Host "Day 1 smoke check passed."
