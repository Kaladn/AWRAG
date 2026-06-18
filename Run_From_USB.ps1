param(
    [string]$RuntimeRoot = "$env:USERPROFILE\AWRAG_Runtime",
    [string]$DatasetId = "local_dataset"
)

$ErrorActionPreference = "Stop"
$packageRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$env:PYTHONPATH = (Join-Path $packageRoot "src")

Write-Host "AWRAG reviewer demo package: $packageRoot"
Write-Host "Runtime root: $RuntimeRoot"
Write-Host "Dataset id: $DatasetId"
Write-Host ""
python -m awrag.cli init --runtime-root $RuntimeRoot --dataset-id $DatasetId
Write-Host ""
Write-Host "Next:"
Write-Host "  python -m awrag.cli intake --runtime-root `"$RuntimeRoot`" --dataset-id `"$DatasetId`" --source <local-doc-folder>"
Write-Host "  python -m awrag.cli query --runtime-root `"$RuntimeRoot`" --dataset-id `"$DatasetId`" --question `"What does this data say?`""
