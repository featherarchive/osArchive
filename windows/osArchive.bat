@echo off
setlocal
cd /d "%~dp0.."

py -3 -m osint_tool
if errorlevel 1 (
    echo.
    echo osArchive failed to start.
    echo Make sure Python 3.11 or newer is installed and run:
    echo py -3 -m pip install -e .
    pause
)
