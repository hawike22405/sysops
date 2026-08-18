@echo off
setlocal

:: Check if the required packages are installed
python -c "import rich; import psutil" 2>nul
if %ERRORLEVEL% neq 0 (
    echo [sysops] Missing requirements detected. Installing them automatically...
    python -m pip install -q .
    if %ERRORLEVEL% neq 0 (
        echo [sysops] Failed to install requirements. Please ensure Python and pip are installed.
        pause
        exit /b 1
    )
)

:: Run sysops with any arguments passed to this script
python -m sysops %*
