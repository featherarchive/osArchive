$ErrorActionPreference = "Stop"
Set-Location (Join-Path $PSScriptRoot "..")

try {
    py -3 -m osint_tool
}
catch {
    Write-Host ""
    Write-Host "osArchive failed to start."
    Write-Host "Make sure Python 3.11 or newer is installed and run:"
    Write-Host "py -3 -m pip install -e ."
    Read-Host "Press Enter to exit"
}
