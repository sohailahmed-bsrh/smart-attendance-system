@echo off
echo ==================================================
echo Smart Attendance System - Web Application Startup
echo ==================================================
echo.

echo [1/3] Checking environment...
if not exist "venv\Scripts\python.exe" (
    echo Error: venv not found! Please make sure you are in the project folder.
    pause
    exit /b
)

echo [2/3] Installing required packages...
call .\venv\Scripts\pip.exe install -r requirements.txt
if %errorlevel% neq 0 (
    echo [Warning] Some packages might have failed to install cleanly, trying to run anyway...
) else (
    echo Packages installed successfully!
)

echo.
echo [3/3] Starting the Enterprise Desktop Application...
echo.

.\venv\Scripts\python.exe main.py

echo.
echo Server has stopped or crashed. See any errors above.
pause
