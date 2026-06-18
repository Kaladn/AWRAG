param(
    [string]$InstallPath = "$env:USERPROFILE\AWRAG_Reviewer_Demo"
)

$ErrorActionPreference = "Stop"
$source = Split-Path -Parent $MyInvocation.MyCommand.Path
$target = [System.IO.Path]::GetFullPath($InstallPath)

New-Item -ItemType Directory -Path $target -Force | Out-Null
robocopy $source $target /E /XD .git .pytest_cache __pycache__ /XF *.pyc | Out-Null
if ($LASTEXITCODE -gt 7) {
    throw "robocopy failed with exit code $LASTEXITCODE"
}

python -m pip install -e $target

Write-Host "AWRAG reviewer demo installed to: $target"
Write-Host "Create a local runtime outside the install folder, then run:"
Write-Host "  awrag init --runtime-root <local-runtime> --dataset-id reviewer_docs"
Write-Host "  awrag intake --runtime-root <local-runtime> --dataset-id reviewer_docs --source <local-doc-folder>"
Write-Host "  awrag query --runtime-root <local-runtime> --dataset-id reviewer_docs --question `"What does this data say?`""
