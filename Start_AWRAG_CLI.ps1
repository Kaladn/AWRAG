$ErrorActionPreference = "Stop"

$PackageRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$env:PYTHONPATH = Join-Path $PackageRoot "src"

Write-Host ""
Write-Host "AnchorWorks / AWRAG Reviewer CLI" -ForegroundColor Cyan
Write-Host "Package: $PackageRoot"
Write-Host "Count backend: awrag_native_binary_counts@1"
Write-Host "Symbol system: awrag_public_6b@1"
Write-Host ""
Write-Host "Suggested local runtime:"
Write-Host "  `$runtime = `"$env:USERPROFILE\AWRAG_Runtime`""
Write-Host ""
Write-Host "Commands:"
Write-Host "  python -m awrag.cli --help"
Write-Host "  python -m awrag.cli init --runtime-root `$runtime --dataset-id <dataset-id>"
Write-Host "  python -m awrag.cli intake --runtime-root `$runtime --dataset-id <dataset-id> --source <local-doc-folder>"
Write-Host "  python -m awrag.cli status --runtime-root `$runtime --dataset-id <dataset-id>"
Write-Host "  python -m awrag.cli query --runtime-root `$runtime --dataset-id <dataset-id> --question `"What does this data say?`""
Write-Host ""
Write-Host "Opening CLI help now..." -ForegroundColor Yellow
Write-Host ""

python -m awrag.cli --help
