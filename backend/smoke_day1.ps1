param(
    [switch]$SkipBuild,
    [switch]$SkipReindex
)

$ErrorActionPreference = "Stop"

function Run-Compose {
    param(
        [string]$Label,
        [string[]]$Args
    )

    Write-Host "==> $Label"
    docker @Args
    if ($LASTEXITCODE -ne 0) {
        throw "Step failed: $Label (exit code $LASTEXITCODE)"
    }
}

$repoRoot = Split-Path -Parent $PSScriptRoot
Push-Location $repoRoot

try {
    if (-not $SkipBuild) {
        Run-Compose -Label "Building backend image" -Args @("compose", "build", "backend")
    }

    if (-not $SkipReindex) {
        Run-Compose -Label "Rebuilding vector index" -Args @("compose", "run", "--rm", "backend", "python", "ingest.py", "--force")
    }

    Run-Compose -Label "Running Day 1 RAG checkpoint" -Args @("compose", "run", "--rm", "backend", "python", "test_rag.py")
    Write-Host "Day 1 smoke check passed."
}
finally {
    Pop-Location
}
