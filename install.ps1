<#
    Windows installer for sysops (PowerShell equivalent of install.sh).

    Usage:
        irm https://raw.githubusercontent.com/hawike22405/sysops/main/install.ps1 | iex
#>

if ($PSVersionTable.PSVersion.Major -lt 5) {
    Write-Host "ERROR: PowerShell 5.0 or later is required (found $($PSVersionTable.PSVersion))." -ForegroundColor Red
    exit 1
}

$ErrorActionPreference = "Stop"

$RepoUrl    = "https://github.com/hawike22405/sysops.git"
$InstallDir = if ($env:SYSOPS_INSTALL_DIR) { $env:SYSOPS_INSTALL_DIR } else { Join-Path $env:USERPROFILE ".local\share\sysops" }
$BinDir     = if ($env:SYSOPS_BIN_DIR)     { $env:SYSOPS_BIN_DIR }     else { Join-Path $env:USERPROFILE ".local\bin" }
$VenvDir    = Join-Path $InstallDir ".venv"
$SrcDir     = Join-Path $InstallDir "src-checkout"

function Info($msg) { Write-Host "==> $msg" -ForegroundColor Cyan }
function Warn($msg) { Write-Host "!! $msg" -ForegroundColor Yellow }
function Err($msg)  { Write-Host "ERROR: $msg" -ForegroundColor Red }

$pythonCmd  = $null
$pythonArgs = @()

foreach ($candidate in @("python", "python3")) {
    if (Get-Command $candidate -ErrorAction SilentlyContinue) {
        $pythonCmd = $candidate
        break
    }
}
if (-not $pythonCmd -and (Get-Command py -ErrorAction SilentlyContinue)) {
    $pythonCmd  = "py"
    $pythonArgs = @("-3")
}
if (-not $pythonCmd) {
    Err "Python 3 is required but was not found on PATH."
    exit 1
}

$pyVersion = & $pythonCmd @pythonArgs -c "import sys; print('%d.%d' % sys.version_info[:2])"
Info "Found $pythonCmd $pyVersion"

if (-not (Get-Command git -ErrorAction SilentlyContinue)) {
    Err "git is required to fetch sysops but was not found on PATH."
    exit 1
}

New-Item -ItemType Directory -Force -Path $InstallDir | Out-Null

if (Test-Path (Join-Path $SrcDir ".git")) {
    Info "Updating existing sysops source"
    git -C $SrcDir fetch --depth 1 origin main
    if ($LASTEXITCODE -ne 0) { throw "Failed to fetch latest sysops source" }
    git -C $SrcDir reset --hard origin/main
    if ($LASTEXITCODE -ne 0) { throw "Failed to reset source to origin/main" }
} else {
    Info "Cloning latest sysops source"
    if (Test-Path $SrcDir) { Remove-Item -Recurse -Force $SrcDir }
    git clone --depth 1 --branch main $RepoUrl $SrcDir
    if ($LASTEXITCODE -ne 0) { throw "Failed to clone sysops repository" }
}

if (-not (Test-Path (Join-Path $SrcDir "src\sysops\cli.py"))) {
    throw "Latest source does not contain src\sysops\cli.py"
}

if (Test-Path $VenvDir) {
    Info "Removing previous virtual environment"
    Remove-Item -Recurse -Force $VenvDir
}

Info "Creating virtual environment at $VenvDir"
& $pythonCmd @pythonArgs -m venv $VenvDir
if ($LASTEXITCODE -ne 0) { throw "Failed to create virtual environment" }

$venvPython = Join-Path $VenvDir "Scripts\python.exe"
& $venvPython -m pip install --upgrade pip --quiet
if ($LASTEXITCODE -ne 0) { throw "Failed to upgrade pip" }

Info "Installing latest sysops source"
& $venvPython -m pip install --quiet --no-cache-dir $SrcDir
if ($LASTEXITCODE -ne 0) { throw "Failed to install sysops" }

New-Item -ItemType Directory -Force -Path $BinDir | Out-Null

$asciiCheck = & $venvPython -c "import sysops; from sysops.cli import build_parser; build_parser(); print(sysops.__file__)"
if ($LASTEXITCODE -ne 0) {
    throw "Could not verify the installed sysops CLI"
}

$shimPath = Join-Path $BinDir "sysops.cmd"
$shimContent = @"
@echo off
"$venvPython" -m sysops %*
"@
Set-Content -Path $shimPath -Value $shimContent -Encoding ASCII -Force

$legacyExe = Join-Path $BinDir "sysops.exe"
if (Test-Path $legacyExe) {
    try {
        Remove-Item -Force $legacyExe
        Info "Removed stale sysops.exe launcher"
    } catch {
        Warn "Could not remove stale launcher: $legacyExe"
    }
}

# Remove stale launchers that can shadow the managed sysops command.
$staleLocations = @(
    (Join-Path $env:USERPROFILE ".local\bin\sysops.ps1"),
    (Join-Path $env:LOCALAPPDATA "Programs\Python\Python312\Scripts\sysops.exe")
)
foreach ($stale in $staleLocations) {
    if (Test-Path $stale) {
        try {
            Remove-Item -Force $stale
            Info "Removed stale launcher: $stale"
        } catch {
            Warn "Could not remove stale launcher: $stale"
        }
    }
}

# Put the managed sysops directory FIRST in the current and user PATH.
$userPath = [Environment]::GetEnvironmentVariable("Path", "User")
$entries = @()
if ($userPath) {
    $entries = $userPath -split ';' | Where-Object {
        $_ -and ($_ -ne $BinDir)
    }
}
$newUserPath = (@($BinDir) + $entries) -join ';'
[Environment]::SetEnvironmentVariable("Path", $newUserPath, "User")

$currentEntries = $env:Path -split ';' | Where-Object {
    $_ -and ($_ -ne $BinDir)
}
$env:Path = (@($BinDir) + $currentEntries) -join ';'

Info "Installed sysops to $BinDir\sysops.cmd"
Info "Managed sysops directory is first in PATH: $BinDir"
Info "Close and reopen PowerShell, then run: sysops --help"
