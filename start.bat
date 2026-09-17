@echo off
TITLE KhananRakshak (CoalGuard AI) - 1-Click Launcher
echo ============================================================
echo   KhananRakshak: Smart Governance Platform for Coal Mines
echo ============================================================
echo.

:: Check if Python is installed
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python is not installed or not added to PATH!
    echo Please install Python 3.10 or higher from https://python.org
    echo Make sure to check the box "Add Python to PATH" during installation.
    pause
    exit /b
)

echo [1/3] Checking Python installation... OK.
echo.
echo [2/3] Installing/Verifying required dependencies...
python -m pip install -r requirements.txt
if %errorlevel% neq 0 (
    echo [WARNING] Some dependencies failed to install. Retrying with basic packages...
    python -m pip install fastapi uvicorn pydantic python-multipart jinja2
)

echo.
echo [3/3] Launching KhananRakshak Server...
echo.
echo ============================================================
echo   Server is running at: http://127.0.0.1:8000
echo   Swagger API Docs at:  http://127.0.0.1:8000/docs
echo ============================================================
echo.
echo Opening the web application in your default browser...
start http://127.0.0.1:8000

python run.py
pause
