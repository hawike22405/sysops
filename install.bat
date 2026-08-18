@echo off
echo Installing sysops and its requirements...
python -m pip install .

if %ERRORLEVEL% equ 0 (
    echo.
    echo =======================================================
    echo sysops installed successfully!
    echo You can now run the 'sysops' command in your terminal.
    echo =======================================================
) else (
    echo.
    echo =======================================================
    echo Installation failed. 
    echo Please ensure Python is installed and added to your PATH.
    echo =======================================================
)
pause
