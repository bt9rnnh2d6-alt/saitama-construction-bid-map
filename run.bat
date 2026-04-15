@echo off
chcp 65001 > nul
title Saitama Construction Bid Info Map

echo ============================================================
echo  Saitama Construction Bid Info Map
echo  (Saitama Kensetsu Kouji Nyusatsu Joho Map)
echo ============================================================
echo.

python --version > nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python is not installed.
    echo.
    echo Please install Python from https://www.python.org/downloads/
    echo Make sure to check "Add Python to PATH" during installation.
    echo.
    pause
    exit /b 1
)

echo [1/3] Checking required libraries...
python -m pip install requests beautifulsoup4 --quiet 2>nul
echo Done.

echo.
echo [2/3] Fetching bid data... (first run may take a few minutes)
echo.
python scraper.py
if %errorlevel% neq 0 (
    echo.
    echo [ERROR] Data fetch failed. See messages above.
    pause
    exit /b 1
)

echo.
echo [3/3] Starting map server
echo ============================================================
echo  Opening http://localhost:8765/ in your browser
echo  Keep this window open while using the app
echo  Close this window to stop the server
echo ============================================================
echo.

rem Schedule browser to open after 2 seconds (wait for server startup)
start "" /b cmd /c "timeout /t 2 /nobreak > nul && start """" ""http://localhost:8765/"""

rem Start the server (runs until window is closed)
python server.py

rem Keep window open if server exits so errors can be read
echo.
echo ============================================================
echo  Server stopped.
echo  If there are error messages above, please check them.
echo ============================================================
pause
