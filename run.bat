@echo off
REM NetDoctor - Windows launch script
REM Ensures dependencies are installed, then launches the app.

setlocal

set "SCRIPT_DIR=%~dp0"
cd /d "%SCRIPT_DIR%"

echo "NetDoctor - launching..."

REM Check Python
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Python is not installed or not on PATH.
    echo Please install Python 3.11+ from https://python.org and try again.
    pause
    exit /b 1
)

REM Install dependencies if requirements.txt exists
if exist requirements.txt (
    echo Installing/updating dependencies...
    python -m pip install -r requirements.txt
    if %errorlevel% neq 0 (
        echo WARNING: Failed to install some dependencies.
    )
)

REM Launch the application
echo Starting NetDoctor...
start "" python main.py

endlocal
