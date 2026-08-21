# Repairs a Windows SysOps installation after a self-update executable-lock failure.
$ErrorActionPreference = "Stop"

Write-Host "Closing running sysops processes..." -ForegroundColor Cyan
Get-Process sysops -ErrorAction SilentlyContinue | ForEach-Object {
    Write-Host "  Stopping PID $($_.Id)"
    Stop-Process -Id $_.Id -Force
}
Start-Sleep -Milliseconds 750

$installDir = if ($env:SYSOPS_INSTALL_DIR) { $env:SYSOPS_INSTALL_DIR } else { Join-Path $env:USERPROFILE ".local\share\sysops" }
$venvPython = Join-Path $installDir ".venv\Scripts\python.exe"
$sourceDir = Join-Path $installDir "src-checkout"

if (-not (Test-Path $venvPython)) {
    throw "Could not find SysOps virtual environment: $venvPython"
}
if (-not (Test-Path (Join-Path $sourceDir "pyproject.toml"))) {
    throw "Could not find the SysOps source checkout: $sourceDir"
}

Write-Host "Installing the latest SysOps source..." -ForegroundColor Cyan
& $venvPython -m pip install --upgrade "$sourceDir"
if ($LASTEXITCODE -ne 0) {
    throw "SysOps installation failed."
}

Write-Host "SysOps repair complete. Run: sysops update" -ForegroundColor Green
