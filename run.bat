@echo off
setlocal

:: Check if the required packages are installed
python -c "import psutil; import rich; import distro; import PIL" 2>nul
if %ERRORLEVEL% neq 0 (
    echo [sysops] Missing requirements detected. Installing them automatically...
    python -m pip install -q .
    if %ERRORLEVEL% neq 0 (
        echo [sysops] Failed to install requirements. Please ensure Python and pip are installed.
        pause
        exit /b 1
    )
)

:: Run sysops through its installed module entry point
python -c "from sysops.cli import main; main()" %*
if %ERRORLEVEL% neq 0 (
    echo [sysops] Failed to start.
    pause
    exit /b %ERRORLEVEL%
)
