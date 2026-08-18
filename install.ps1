#Requires -Version 5.0
<#
    Windows installer/update script for sysops.

    Usage:
        irm https://raw.githubusercontent.com/hawike22405/sysops/main/install.ps1 | iex
#>

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
    git -C $SrcDir reset --hard origin/main
} else {
    Info "Cloning latest sysops source"
    if (Test-Path $SrcDir) { Remove-Item -Recurse -Force $SrcDir }
    git clone --depth 1 --branch main $RepoUrl $SrcDir
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

$venvExe = Join-Path $VenvDir "Scripts\sysops.exe"
if (-not (Test-Path $venvExe)) {
    Err "Install finished but $venvExe was not found."
    exit 1
}

# Verify the installed package, not just the source tree, exposes the ascii command.
$asciiCheck = & $venvPython -c "from sysops.cli import build_parser; print('ascii' in build_parser()._subparsers._group_actions[0].choices)"
if ($LASTEXITCODE -ne 0 -or $asciiCheck.Trim() -ne "True") {
    throw "The installed sysops package does not contain the 'ascii' command."
}

$shimPath = Join-Path $BinDir "sysops.cmd"
$shimContent = '@echo off' + "`r`n" + '"' + $venvExe + '" %*' + "`r`n"
Set-Content -Path $shimPath -Value $shimContent -Encoding ASCII -Force

$stalePs1 = Join-Path $BinDir "sysops.ps1"
if (Test-Path $stalePs1) { Remove-Item -Force $stalePs1 }

$userPath = [Environment]::GetEnvironmentVariable("Path", "User")
$pathEntries = @()
if ($userPath) {
    $pathEntries = $userPath -split ';' | Where-Object { $_ -and ($_ -ne $BinDir) }
}
[Environment]::SetEnvironmentVariable("Path", (($BinDir + $pathEntries) -join ';'), "User")
$env:Path = "$BinDir;$env:Path"

Info "Installed sysops to $venvExe"
Info "ASCII subcommand verified successfully"
Info "Close and reopen PowerShell, then run: sysops ascii <image>"
