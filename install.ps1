#Requires -Version 5.0
<#
    Windows installer for sysops (PowerShell equivalent of install.sh).

    Usage:
        irm https://raw.githubusercontent.com/hawike22405/sysops/main/install.ps1 | iex
#>

$ErrorActionPreference = "Stop"

$RepoUrl    = "https://github.com/hawike22405/sysops.git"
$InstallDir = if ($env:SYSOPS_INSTALL_DIR) { $env:SYSOPS_INSTALL_DIR } else { Join-Path $env:USERPROFILE ".local\share\sysops" }
$BinDir     = if ($env:SYSOPS_BIN_DIR)     { $env:SYSOPS_BIN_DIR }     else { Join-Path $env:USERPROFILE ".local\bin" }
$VenvDir    = Join-Path $InstallDir ".venv"

function Info($msg) { Write-Host "==> $msg" -ForegroundColor Cyan }
function Warn($msg) { Write-Host "!! $msg" -ForegroundColor Yellow }
function Err($msg)  { Write-Host "ERROR: $msg" -ForegroundColor Red }

# --- locate a usable Python 3 -------------------------------------------------
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
    Err "Install it from https://www.python.org/downloads/ and make sure 'Add python.exe to PATH' is checked, then re-run this installer."
    exit 1
}

$pyVersion = & $pythonCmd @pythonArgs -c "import sys; print('%d.%d' % sys.version_info[:2])"
Info "Found $pythonCmd $pyVersion"

# --- decide source: local checkout vs fresh git clone -------------------------
$scriptDir = $null
if ($PSCommandPath) { $scriptDir = Split-Path -Parent $PSCommandPath }
if (-not $scriptDir) { $scriptDir = (Get-Location).Path }

if ((Test-Path (Join-Path $scriptDir "pyproject.toml")) -and (Test-Path (Join-Path $scriptDir "src\sysops"))) {
    $srcDir = $scriptDir
    Info "Using local source at $srcDir"
} else {
    if (-not (Get-Command git -ErrorAction SilentlyContinue)) {
        Err "git is required to fetch sysops but was not found on PATH."
        Err "Install it from https://git-scm.com/download/win and re-run this installer."
        exit 1
    }
    $srcDir = Join-Path $InstallDir "src-checkout"
    Info "Fetching sysops source into $srcDir"
    New-Item -ItemType Directory -Force -Path $InstallDir | Out-Null
    if (Test-Path (Join-Path $srcDir ".git")) {
        git -C $srcDir pull --ff-only
    } else {
        if (Test-Path $srcDir) { Remove-Item -Recurse -Force $srcDir }
        git clone --depth 1 $RepoUrl $srcDir
    }
}

# --- venv + install -------------------------------------------------------------
Info "Setting up virtual environment at $VenvDir"
New-Item -ItemType Directory -Force -Path $InstallDir | Out-Null
& $pythonCmd @pythonArgs -m venv $VenvDir

$venvPython = Join-Path $VenvDir "Scripts\python.exe"
& $venvPython -m pip install --upgrade pip --quiet

Info "Installing sysops"
& $venvPython -m pip install --quiet $srcDir

# --- expose the `sysops` command -------------------------------------------------
# Windows can't rely on a plain symlink without elevated privileges, so we
# generate a tiny .cmd shim that forwards to the venv's installed exe instead.
New-Item -ItemType Directory -Force -Path $BinDir | Out-Null

$venvExe = Join-Path $VenvDir "Scripts\sysops.exe"
if (-not (Test-Path $venvExe)) {
    Err "Install finished but $venvExe was not found. Check the package's entry_points/console_scripts config."
    exit 1
}

$shimPath = Join-Path $BinDir "sysops.cmd"
$shimContent = "@echo off`r`n`"$venvExe`" %*`r`n"
Set-Content -Path $shimPath -Value $shimContent -Encoding ASCII -Force
Info "Linked $shimPath -> $venvExe"

# --- PATH handling ---------------------------------------------------------------
$userPath = [Environment]::GetEnvironmentVariable("Path", "User")
if ($userPath -notlike "*$BinDir*") {
    Warn "$BinDir is not on your PATH yet."
    $newPath = if ([string]::IsNullOrEmpty($userPath)) { $BinDir } else { "$userPath;$BinDir" }
    [Environment]::SetEnvironmentVariable("Path", $newPath, "User")
    $env:Path = "$env:Path;$BinDir"
    Warn "Added $BinDir to your User PATH."
    Warn "Open a NEW terminal window for this to take effect, then run: sysops"
} else {
    Info "Install complete! Run it with: sysops"
}
