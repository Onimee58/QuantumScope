# Optional PowerShell entrypoint; avoids requiring execution-policy changes by default.
$ErrorActionPreference = 'Stop'
Set-Location $PSScriptRoot
& (Join-Path $PSScriptRoot 'install_and_run_windows.bat')
exit $LASTEXITCODE
